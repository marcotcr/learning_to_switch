#!/usr/bin/python
"""Runs the whole STREAM recommender. The following must be provided:
  - List of algorithms to be used as level-1 predictors (default == all)
  - Dataset locations: path of the datasets to be used
  - Itens attributes file location
  - Users attributes file location
  - Output path 

  With it, the script will run the following:
  - Split dataset into 5-fold validation
  - Run Level-1 recommenders for each provided algorithm
  - generate the RunTimeMetrics to be used
  - Generate input in Weka format
  - Run Linear regression as level-2 predictor
  - Parse the output from Weka to the same format used from MyMediaLite

    Author: Arthur Barbosa C^amara (camara.arthur@{gmail.com, dcc.ufmg.br})
"""

import sys
import os
import getopt

def Usage():
  print sys.argv[0]
  print "Options:"
  print "-a (optional) List of algorithms to be used as level-1 predictors. Default all"
  print "-i (required) Location of the dataset to be used"
  print "-o (required) Output folder"
  print "-t (optional) Location of the itens attributes file. In a formate recognized by MyMediaLite"
  print "-u (optional) Location of the users attributes file"
  print "-w (required) Location of weka.jar file"
  print "Example Usage:"
  print "./run_linear.py -a BiPolarSlopeOne,UserKNN,SVDPlusPlus -i /mnt/hd0/marcotcr/datasets/MovieLens1M/ratings.dat -o ./output/ -t /mnt/hd0/marcotcr/datasets/MovieLens1M/moviesok.dat -u /mnt/hd0/marcotcr/datasets/MovieLens1M/usersok.dat"
  print ""
  sys.exit(2)

def List2String(list):
  """Generates a comma-separated string, based on a list
    """
  list = str(list)
  list = list.replace("]","")
  list = list.replace("[","")
  list = list.replace("', '", ",")
  list = list.replace("'", "")
  return list
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "a:i:o:t:u:w:")
  except getopt.GetoptError, err:
      print str(err)
      Usage()

  dataset              = None
  out_folder           = None
  item_attributes_file = None
  user_attribures_file = None
  weka_path            = None
  option               = None
  algorithms  = ['BiPolarSlopeOne', 'FactorWiseMatrixFactorization',
               'GlobalAverage', 'ItemAttributeKNN', 'ItemAverage', 'ItemKNN',
               'MatrixFactorization', 'SlopeOne', 'UserAttributeKNN', 'UserAverage',
               'UserItemBaseline', 'UserKNN', 'TimeAwareBaseline',
               'TimeAwareBaselineWithFrequencies', 'CoClustering',
               'LatentFeatureLogLinearModel', 'BiasedMatrixFactorization', 'SVDPlusPlus',
               'SigmoidSVDPlusPlus', 'SigmoidItemAsymmetricFactorModel',
               'SigmoidUserAsymmetricFactorModel']

  for option, value in opts:
    if option == "-a":
      algorithms = value.split(",")
    elif option == "-i":
      dataset = value
    elif option == "-o":
      out_folder = value
    elif option == "-t":
      item_attributes_file = value
    elif option == "-u":
      user_attribures_file = value
    elif option == "-w":
      weka_path = value
    else:
      assert False, "Option is not avaiable"
  if not dataset or not out_folder or not weka_path:
    Usage()

  if not os.path.exists(out_folder):
    os.makedirs(out_folder)
#first things first. With the dataset, split it to cross-folding validation.
#They will be generated at <output>/lvl1cv/r<nth-fold>.<test|train>
  if not os.path.exists(out_folder+"lvl1cv"):
    os.makedirs(out_folder+"lvl1cv")
  level1_cross_validation_folder = (("%slvl1cv/r") % (out_folder))
  cmd = (("./generate_cv.py -i %s -o %s") % (dataset, level1_cross_validation_folder))
  print cmd
  #os.system(cmd)

#Now, with the dataset in a 5 fold fashion, run all the level-1 predictors required. Using MyMediaLite.


  if len(algorithms) == 21:
    for i in range(1,6):
      in_file = level1_cross_validation_folder+str(i)
      out_file = (("%slvl1out/r%d") % (out_folder, i))
      if not os.path.exists(out_file):
        os.makedirs(out_file)
      cmd = (("./level1_predictors.py -t %s -o %s -i %s -u %s") % (in_file, out_file, item_attributes_file, user_attribures_file))
      print cmd
      #os.system(cmd)
  else:
    for i in range(1,6):
      in_file = level1_cross_validation_folder+str(i)
      out_file = (("%slvl1out/r%d") % (out_folder, i))
      if not os.path.exists(out_file):
        os.makedirs(out_file)
      cmd = (("./level1_predictors.py -a %s -t %s -o %s -i %s -u %s") % (List2String(algorithms), in_file, out_file, item_attributes_file, user_attribures_file))
      print cmd
      #os.system(cmd)

#Now we are done with the level-1 predictors. Next steps are: Generate the RunTimeMetrics and the input files for weka:
  for i in range (1,6):
    in_file       = (("%slvl1out/r%d/") % (out_folder, i))
    train_file    = (("%s%d_train")%(level1_cross_validation_folder, i))
    test_file     = (("%s%d_test")%(level1_cross_validation_folder, i))
    out_file      = (("%swekaout%d")%(out_folder, i))
    if len(algorithms) == 21:
      cmd = ("./generate_weka.py -i %s -u %s -t %s -f %s -e %s -o %s")%(in_file, user_attribures_file, item_attributes_file, train_file, test_file, out_file)

    else:
      cmd = ("./generate_weka.py -a %s -i %s -u %s -t %s -f %s -e %s -o %s")%(List2String(algorithms), in_file, user_attribures_file, item_attributes_file, train_file, test_file, out_file)
    print cmd
    os.system(cmd)

#Now, run linear regression usint weka output files
  for i in range(1,6):
    raw_input("running generate_weka...")
    test_file  = (("%swekaout%dtest.arff") %(out_folder, i))
    train_file = (("%swekaout%dtrain.arff")% (out_folder, i))
    cmd = (("java -Xmx2000m -cp %s weka.classifiers.meta.FilteredClassifier -F weka.filters.unsupervised.attribute.RemoveType -W weka.classifiers.functions.LinearRegression -t %s -T %s -i -k -p 1 > streamout%d.txt")%(weka_path, train_file, test_file, i))
    print cmd
    #os.system(cmd)


if __name__ == "__main__":
  main()
