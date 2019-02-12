import argparse
import operator
import sys
import tensorflow as tf
import data_provider as data_provider

k_data_folder = './data/minute_data/'

def analyze_data_quality_through_time(argv):
  """Analyze crawled data through time. Print stats for number of symbols that have more than 50 data points. """
  start_date = 20190101
  end_date = 20191231
  start_date_dict, end_date_dict, count_dict, valid_count_dict = {}, {}, {}, {}

  dp = data_provider.DataProvider(FLAGS.data_folder, True)
  all_sub_folders = dp.get_all_available_dates()
  for str_date_val in all_sub_folders:
    date_val = int(str_date_val)
    if date_val < start_date or date_val > end_date:
      continue
    dp.load_one_day_data(str_date_val)
    one_day_list = dp.get_available_symbol_list()
    for symbol in one_day_list:
      if symbol not in start_date_dict:
        start_date_dict[symbol] = date_val
        end_date_dict[symbol] = date_val
        count_dict[symbol] = 1
        valid_count_dict[symbol] = 0
      count_dict[symbol] += 1
      start_date_dict[symbol] = min(date_val, start_date_dict[symbol])
      end_date_dict[symbol] = max(date_val, end_date_dict[symbol])
    print('Date: %s, number of symbols: %d' % (str_date_val, len(one_day_list)))

  if FLAGS.show_per_symbol_stats:
    for iter in sorted(count_dict.items(), key=operator.itemgetter(1)):
      symbol = iter[0]
      print('%s %d %d %d %d' % (symbol, start_date_dict[symbol], end_date_dict[symbol], count_dict[symbol],
                                valid_count_dict[symbol]))

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--data_folder',
    type=str,
    default=k_data_folder,
    help='Root for historical data'
  )
  parser.add_argument(
    '--show_per_symbol_stats',
    type=bool,
    default=False,
    help='Whether to show symbol stats'
  )
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=analyze_data_quality_through_time, argv=[sys.argv[0]] + unparsed)