import argparse
import os, sys
import tensorflow as tf

import matplotlib.pyplot as plt

import util.data_provider as data_provider
import util.datetime_util as datetime_util
import util.distribution_analyzer as distribution_analyzer
import proto.stock_pb2 as stock_pb2
import proto.nn_train_param_pb2 as nn_train_param_pb2

import train.model_manager as model_manager

k_data_folder = './data/intra_day/'
k_png_temp_folder = 'temppng/'
k_distribution_bin_size = 0.001
k_price_drop_watch_time = 30
k_drop_threshold = -0.02


def export_some_intra_day_data_to_pngs():
  dp = data_provider.DataProvider(FLAGS.data_dir)
  dp.batch_output_one_day_data_to_png(20180427, k_png_temp_folder)

def analyze_distribution():
  if not os.path.isdir(k_png_temp_folder):
    os.makedirs(k_png_temp_folder)
  
  dp = data_provider.DataProvider(FLAGS.data_dir)
  subfolder_list = dp.get_all_available_subfolder()
  
  for subfolder in subfolder_list:
    print('Now analyzing {0}'.format(subfolder))
    da1 = distribution_analyzer.OpenCloseDistributionAnalyzer(subfolder, k_distribution_bin_size)
    da2 = distribution_analyzer.PriceDropAtBeginningDistributionAnalyzer(subfolder,
      k_distribution_bin_size, k_price_drop_watch_time, k_drop_threshold)
    da3 = distribution_analyzer.PriceDropAtBeginningClosePriceAsChangeDistributionAnalyzer(
      subfolder, k_distribution_bin_size, k_price_drop_watch_time, k_drop_threshold)
      
    symbol_list = dp.get_symbol_list_for_a_day(subfolder)
    for symbol in symbol_list:
      result, one_stock_data = dp.deserialize_one_symbol(subfolder, symbol)
      if not result:
        print('Failed to deserialize symbol {0} on day {1}'.format(symbol, subfolder))
        continue
      da1.add_one_stock_for_distribution(symbol, one_stock_data)
      da2.add_one_stock_for_distribution(symbol, one_stock_data)
      da3.add_one_stock_for_distribution(symbol, one_stock_data)
    img_path = os.path.join(k_png_temp_folder, subfolder + '.png')
    da1.export_distribution_to_png(img_path)
    img_path = os.path.join(k_png_temp_folder, '{0}_{1}_{2}'.format(subfolder, k_price_drop_watch_time, k_drop_threshold) + '.png')
    da2.export_distribution_to_png(img_path)
    img_path = os.path.join(k_png_temp_folder, '{0}_{1}_{2}_eod'.format(subfolder, k_price_drop_watch_time, k_drop_threshold) + '.png')
    da3.export_distribution_to_png(img_path)
  return

def compare_two_crawl_result():
  """ Compare two crawled folder and print number of timepoints for each stock. """
  folder1 = './data/intra_day/'
  folder2 = './data/intra_day_backup/'
  interested_date = 20180524

  dp1 = data_provider.DataProvider(folder1)
  dp2 = data_provider.DataProvider(folder2)

  symbol_list1 = dp1.get_symbol_list_for_a_day(interested_date)
  symbol_list2 = dp2.get_symbol_list_for_a_day(interested_date)

  print ('All symbol number for {0}: {1}, {2}: {3}'.format(folder1, len(symbol_list1), folder2, len(symbol_list2)))

  overlap_symbol = dict()
  for symbol in symbol_list1:
    if symbol in symbol_list2:
      overlap_symbol[symbol] = True
  print ('Overlapped symbol count: {0}'.format(len(overlap_symbol)))

  dp1.load_one_day_data(interested_date)
  dp2.load_one_day_data(interested_date)
  for symbol in overlap_symbol:
    one_data1 = dp1.get_one_symbol_data(symbol)
    one_data2 = dp2.get_one_symbol_data(symbol)
    print('Compare {0}: length1: {1}, length2: {2}'.format(symbol, len(one_data1.data), len(one_data2.data)))

def update_eligible_list():
  dp = data_provider.DataProvider('./data/intra_day/', False)
  day_int_val = 20180417
  dp.load_one_day_data(day_int_val)
  dp.generate_eligible_list()

def analyze_volume_timepoint():
  """Analyze the distribution of volume, number of available timepoints, and cash flow. """
  dp =  data_provider.DataProvider('./data/intra_day/', False)
  day_int_val = 20180502
  symbol_list = dp.get_symbol_list_for_a_day(day_int_val)
  dp.load_one_day_data(day_int_val)
  dp.generate_eligible_list()
  live_trade_folder = os.path.join('./live_trade/', str(day_int_val) + '/')
  
  volume_list, timepoint_list, trade_cash_list = [], [], []

  # we assume that for large symbols, at least $20K should be traded within one minute.
  large_symbol_threshold = 20000 * 60 * 6.5

  num_small_symbol = 0

  for symbol in symbol_list:
    one_symbol_data = dp.get_one_symbol_data(symbol)
    total_volume, total_trade_cash_flow = 0, 0
    for one_time_data in one_symbol_data.data:
      total_volume += one_time_data.volume
      total_trade_cash_flow += one_time_data.volume * one_time_data.open
    volume_list.append(total_volume)

    # load from live trade folder as well
    live_crawl_file = os.path.join(live_trade_folder, symbol + '.pb')
    if os.path.isfile(live_crawl_file):
      fid = open(live_crawl_file)
      content = fid.read()
      fid.close()
      one_stock_data = stock_pb2.ServingCrawledData()
      one_stock_data.ParseFromString(content)
      total_volume_live = one_stock_data.data[-1].total_volume
      print('Symbol: {0}'.format(symbol))
      print('Total volume from historical price: {0}, from live crawl: {1}'.format(total_volume, total_volume_live))

    if total_trade_cash_flow > 1e8:
      print('Symbol: {0}, total trade cash flow: ${1}M'.format(symbol, total_trade_cash_flow/1e6))
    else:
      trade_cash_list.append(total_trade_cash_flow)

    if total_trade_cash_flow < large_symbol_threshold:
        num_small_symbol += 1
    timepoint_list.append(len(one_symbol_data.data))

  print('Total number of small symbols: {0}'.format(num_small_symbol))
  plt.plot(timepoint_list, volume_list, '.')
  plt.xlim(0, max(timepoint_list))
  plt.xlabel('Number of time points')
  plt.ylim(0, max(volume_list))
  plt.ylabel('Daily traded volume')
  plt.grid()
  plt.show()
  plt.clf()
  #plt.plot(trade_cash_list)
  plt.hist(trade_cash_list, bins = 50)
  plt.grid()
  plt.show()

def run_and_display_classifier_prob():
  """ Run NN through some symbols and display their buy probability. """
  use_eligible_list = True
  day_int_val = 20180427
  model_path = './model/threshold_0.005/model_classification_3.ckpt'

  dp =  data_provider.DataProvider(k_data_folder, use_eligible_list)
  symbol_list = dp.get_symbol_list_for_a_day(day_int_val)
  dp.load_one_day_data(day_int_val)

  mm = model_manager.FixedNumTimePointsModelManager()
  mm.init_for_serving()

  num_symbol_to_show = 50

  with tf.Session() as sess:
    saver = tf.train.Saver()
    saver.restore(sess, model_path)
    for symbol in symbol_list:
      one_symbol_data = dp.get_one_symbol_data(symbol)
      time_val_list, price_list, prob_list = [], [], []
      for index in range(0, len(one_symbol_data.data)):
        time_val_list.append(datetime_util.int_to_time(one_symbol_data.data[index].time_val))
        price_list.append(one_symbol_data.data[index].open)
        if mm.is_eligible_to_be_fed_into_network(one_symbol_data, index):
          prob_score = mm.compute_prob(one_symbol_data, index)
          prob_list.append(prob_score)
        else:
          prob_list.append(0.5)
      num_symbol_to_show -= 1
      if num_symbol_to_show < 0:
        break

      plt.subplot(2,1,1)
      plt.plot(time_val_list, price_list)
      plt.grid()
      plt.title(symbol)
      plt.subplot(2,1,2)
      plt.plot(time_val_list, prob_list)
      plt.grid()
      plt.show()
      plt.clf()

def load_model():
  param = nn_train_param_pb2.TrainingParams()
  param.architecture.extend([32, 32])
  param.previous_model = './model/sell_classifier/model_classification_25.ckpt'
  param.num_time_points = 100
  param.upper_time_point_limit = 149
  param.type = nn_train_param_pb2.TrainingParams.CLASSIFY_BUY_SELL_TIME
  with tf.Session() as sess:
    mm = model_manager.FixedNumTimePointsModelManager(param)
    mm.init_for_serving()
    saver = tf.train.Saver(var_list=tf.trainable_variables())
    saver.restore(sess, param.previous_model)
    message = 'Load from previous model {0}'.format(param.previous_model)
    print message

    for variable in tf.trainable_variables():
      print variable


def run_through_analysis_functions(_):
  # export_some_intra_day_data_to_pngs()
  # compare_two_crawl_result()
  # run_and_display_classifier_prob()
  # update_eligible_list()
  compare_two_crawl_result()

if __name__=="__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--data_dir',
    type=str,
    default=k_data_folder,
    help='Root for historical data'
  )
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=run_through_analysis_functions, argv=[sys.argv[0]] + unparsed)
