import argparse
import datetime_util
import matplotlib.pyplot as plt
import os, sys
import tensorflow as tf

import data_provider

k_data_folder = './data/minute_data/'
k_png_temp_folder = 'temppng/'

class DataProviderPngExporter:

  def _prepare_one_stock_data_list(self, one_stock_data):
    time_list, open_list, close_list, high_list, low_list = [], [], [], [], []
    for one_slot_data in one_stock_data.data:
      time_list.append(datetime_util.int_to_time(one_slot_data.time_val))
      open_list.append(one_slot_data.open)
      close_list.append(one_slot_data.close)
      high_list.append(one_slot_data.high)
      low_list.append(one_slot_data.low)
    return time_list, open_list, close_list, high_list, low_list

  def _prepare_display_one_symbol_one_day(self, symbol, one_stock_data, transactions):
    time_list, open_list, close_list, high_list, low_list = self._prepare_one_stock_data_list(one_stock_data)
    k_open_close_line_width = 3
    k_min_max_line_width = 1
    k_epsilon = 0.01
    for k in range(len(time_list)):
      plt.vlines(time_list[k], low_list[k], high_list[k], 'k', linewidth = k_min_max_line_width)
      if open_list[k] < close_list[k]:
        plt.vlines(time_list[k], open_list[k], close_list[k], 'g', linewidth = k_open_close_line_width)
      elif open_list[k] > close_list[k]:
        plt.vlines(time_list[k], open_list[k], close_list[k], 'r', linewidth = k_open_close_line_width)
      else:
        plt.vlines(time_list[k], open_list[k], open_list[k] + k_epsilon, 'g', linewidth = k_open_close_line_width)

    minimal_val = min(low_list)
    maximal_val = max(high_list)
    for transaction in transactions:
      trans_time = datetime_util.int_to_time(transaction.time)
      if transaction.type == stock_pb2.Transaction.BUY:
        plt.vlines(trans_time, minimal_val, maximal_val, 'r')
      else:
        plt.vlines(trans_time, minimal_val, maximal_val, 'b')
    plt.grid()
    plt.title(symbol)

  def export_one_symbol_one_day(self, symbol, one_stock_data, img_path, transactions = []):
    self._prepare_display_one_symbol_one_day(symbol, one_stock_data, transactions)
    plt.savefig(img_path)
    plt.clf()


  def export_some_intra_day_data_to_pngs(self):
    self._dp = data_provider.DataProvider(FLAGS.data_dir, use_eligible_list=False)
    if not os.path.isdir(FLAGS.output_png_dir):
      os.makedirs(FLAGS.output_png_dir)

    # symbol_list = self.get_symbol_list_for_a_day(day_int_val)
    # use the following one to get quick look on major stocks:
    symbol_list = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'ISRG', 'TQQQ', 'BGNE', 'ETSY', 'NVDA']
    print ('Output to png folder %s.' % FLAGS.output_png_dir)
    for symbol in symbol_list:
      print('Processing {0}'.format(symbol))
      result, one_stock_data = self._dp.deserialize_one_symbol(FLAGS.extract_date, symbol)
      if not result:
        print('Not able to deserialize symbol {0}'.format(symbol))
        continue
      png_file_path = os.path.join(FLAGS.output_png_dir, symbol + '.png')
      self.export_one_symbol_one_day(symbol, one_stock_data, png_file_path)

      print('Start Time: {0}'.format(one_stock_data.data[0].time_val))
      print('End Time: {0}'.format(one_stock_data.data[-1].time_val))
      print('No. TimePoints: {0}'.format(len(one_stock_data.data)))

def main(argv):
  del argv
  png_exporter = DataProviderPngExporter()
  png_exporter.export_some_intra_day_data_to_pngs()


if __name__=="__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--data_dir',
    type=str,
    default=k_data_folder,
    help='Root for historical data'
  )
  parser.add_argument(
    '--output_png_dir',
    type=str,
    default=k_png_temp_folder,
    help='Temp png folder output'
  )
  parser.add_argument(
    '--extract_date',
    type=int,
    default=20190107,
    help='Date to be extracted'
  )
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)