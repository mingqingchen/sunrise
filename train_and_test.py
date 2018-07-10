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

  #params.type = nn_train_param_pb2.TrainingParams.CLASSIFY_FUTURE_HIGHEST_PRICE
  params.type = nn_train_param_pb2.TrainingParams.CLASSIFY_BUY_SELL_TIME

  if params.type == nn_train_param_pb2.TrainingParams.CLASSIFY_FUTURE_HIGHEST_PRICE:
    params.upper_time_point_limit = 149
    params.sample_step_training = 1
    params.sample_step_testing = 1
    params.use_relative_price_percentage_to_buy = True
    params.relative_price_percentage = 0.5
  else:
    params.upper_time_point_limit = 14900
    params.sample_step_training = 3
    params.sample_step_testing = 3

  params.open_time = 630
  params.close_time = 1255
  params.total_minutes_normalizer = 390

  params.learning_rate = 2e-4
  params.num_epochs = 250
  params.batch_size = 32

  params.use_cnn = True

  if params.use_cnn:
    params.architecture.extend([4, 8, 4, 8])
  else:
    params.architecture.extend([32, 32])
  
  params.classify_threshold = 0.005

  params.load_previous_model = True
  params.previous_model = 'model_classification_22'

  params.model_folder = './model/'
  params.output_model_name_prefix = 'model'
  params.log_file = './training_log.txt'

  params.local_maximal_window_size = 21;
  params.local_maximal_margin = 0.001;

  params.use_pre_market_data = True

  params.dense_ratio = 0.8
  params.average_cash_flow_per_min = 20000.0

  mm = model_manager.FixedNumTimePointsModelManager(params)
  mm.set_training_dates(20180529, 20180608)
  mm.set_test_dates(20180611, 20180622)
  mm.set_training_data_folder(k_data_folder)
  mm.set_training_use_eligible_list(True)
  mm.train_and_test()

if __name__=="__main__":
  parser = argparse.ArgumentParser()
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
