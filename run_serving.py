import argparse
import os
import sys
import tensorflow as tf

import live_trade.live_trading as live_trading

FLAGS=None

k_data_folder = './data/'

def test_update_refresh_time():
  """ Test refresh time from Google finance. """
  cr = crawler.IntraDayCrawler(k_data_folder)
  symbol_list = cr.get_crawl_list_from_three_indices()
  for symbol in symbol_list:
    result, one_symbol_data = cr.crawl_one_symbol(symbol)
    if not result:
      print('Error crawling symbol {0}'.format(symbol))
    else:
      print('Symbol: {0}'.format(symbol))
      print('Current time: {0}, crawled most updated time: {1}'.format(datetime_util.get_cur_time_int(), one_symbol_data.data[-1].time_val))
      print('Timepoint crawled so far: {0}'.format(len(one_symbol_data.data)))

def main(_):
  trader = live_trading.LiveTrading()
  trader.crawl_forever()
  
if __name__=="__main__":
  parser = argparse.ArgumentParser()
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
