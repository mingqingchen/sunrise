import argparse
import os
import sys
import tensorflow as tf

import crawler
import util.datetime_util as datetime_util

FLAGS=None
k_data_folder = './data/'

def main(_):
  # cr = crawler.IntraDayCrawlerTD(FLAGS.data_folder)
  cr = crawler.IntraDayCrawler(FLAGS.data_folder)
  symbol_list = cr.get_crawl_list_from_three_indices()
  for symbol in symbol_list:
    result, one_symbol_data = cr.crawl_one_symbol(symbol)
    if not result:
      print('Error crawling symbol {0}'.format(symbol))
    else:
      print('Symbol: {0}, Current time: {1}, crawled most updated time: {2}'.format(symbol, datetime_util.get_cur_time_int(), one_symbol_data.data[-1].time_val))
  
if __name__=="__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--data_folder',
    type=str,
    default=k_data_folder,
    help='Root for historical data'
  )
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
