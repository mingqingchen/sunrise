import argparse
import sys
import tensorflow as tf
import data_provider as data_provider

k_data_folder = './data/minute_data/'

def analyze_data_quality_through_time(argv):
  """Analyze crawled data through time. Print stats for number of symbols that have more than 50 data points. """
  start_date = 20190101
  end_date = 20190130
  dp = data_provider.DataProvider(FLAGS.data_folder, False)
  all_sub_folders = dp.get_all_available_dates()
  for sub_folder in all_sub_folders:
    if int(sub_folder) < start_date or int(sub_folder) > end_date:
      continue
    dp.load_one_day_data(sub_folder)
    one_day_list = dp.get_symbol_list_for_a_day(sub_folder)
    num_valid = 0
    for symbol in one_day_list:
      one_symbol_data = dp.get_one_symbol_data(symbol)
      if len(one_symbol_data.data) > 20:
        num_valid += 1
    print('Date: %s, number of symbols: %d, valid ones: %d' % (sub_folder, len(one_day_list), num_valid))


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--data_folder',
    type=str,
    default=k_data_folder,
    help='Root for historical data'
  )
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=analyze_data_quality_through_time, argv=[sys.argv[0]] + unparsed)
