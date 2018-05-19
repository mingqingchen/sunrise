import argparse
import sys
import tensorflow as tf

import train.model_manager as model_manager
import proto.nn_train_param_pb2 as nn_train_param_pb2

FLAGS=None

k_data_folder = './data/intra_day/'

def main(_):
  params = nn_train_param_pb2.TrainingParams()
  params.num_time_points = 100
  params.upper_time_point_limit = 149
  params.open_time = 630
  params.close_time = 1255
  params.total_minutes_normalizer = 390

  params.sample_step_training = 1
  params.sample_step_testing = 1

  params.learning_rate = 1e-3
  params.num_epochs = 250
  params.batch_size = 32

  params.use_cnn = True

  if params.use_cnn:
    params.architecture.extend([8, 16, 8, 16])
  else:
    params.architecture.extend([32, 32])
  params.type = nn_train_param_pb2.TrainingParams.CLASSIFY_FUTURE_HIGHEST_PRICE
  # params.type = nn_train_param_pb2.TrainingParams.CLASSIFY_BUY_SELL_TIME
  params.classify_threshold = 0.005

  params.load_previous_model = False
  params.previous_model = 'model_classification_0'

  params.model_folder = './model/'
  params.output_model_name_prefix = 'model'
  params.log_file = './training_log.txt'

  params.local_maximal_window_size = 21;
  params.local_maximal_margin = 0.001;

  # The following two only applies to CLASSIFY_FUTURE_HIGHEST_PRICE
  params.use_relative_price_percentage_to_buy = True
  params.relative_price_percentage = 0.5

  params.use_pre_market_data = True

  mm = model_manager.FixedNumTimePointsModelManager(params)
  mm.set_training_dates(20180416, 20180420)
  mm.set_test_dates(20180423, 20180430)
  mm.set_training_data_folder(k_data_folder)
  mm.set_training_use_eligible_list(True)
  mm.train_and_test()

if __name__=="__main__":
  parser = argparse.ArgumentParser()
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
