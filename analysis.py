import argparse
import os, sys
import tensorflow as tf

import matplotlib.pyplot as plt

import util.data_provider as data_provider
import util.distribution_analyzer as distribution_analyzer

k_data_folder = './data_test/intra_day/'
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
  folder2 = './data_test/intra_day/'
  interested_date = 20180426

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

def analyze_volume_timepoint():
  """Analyze the distribution of volume, number of available timepoints, and cash flow. """
  dp =  data_provider.DataProvider('./data/intra_day/')
  day_int_val = 20180502
  symbol_list = dp.get_symbol_list_for_a_day(day_int_val)
  dp.load_one_day_data(day_int_val)
  dp.generate_eligible_list()
  
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


def run_through_analysis_functions(_):
  # export_some_intra_day_data_to_pngs()
  # compare_two_crawl_result()
  analyze_volume_timepoint()

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
