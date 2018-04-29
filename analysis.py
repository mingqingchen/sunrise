import argparse
import os, sys
import tensorflow as tf

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

  

def run_through_analysis_functions(_):
  export_some_intra_day_data_to_pngs()
  # compare_two_crawl_result()

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
