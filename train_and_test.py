import argparse
import sys
import tensorflow as tf

import train.model_manager as model_manager

FLAGS=None

k_data_folder = './data/intra_day/'

def main(_):
  mm = model_manager.FixedNumTimePointsModelManager(k_data_folder, True)
  mm.set_training_dates(20180416, 20180420)
  mm.set_test_dates(20180423, 20180423)
  mm.train_and_test()

if __name__=="__main__":
  parser = argparse.ArgumentParser()
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
