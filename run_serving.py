import argparse
import os
import sys
import tensorflow as tf

import crawler
import util.datetime_util as datetime_util

FLAGS=None
k_data_folder = './data/'

def get_multiple_quotes():
  client_id = 'mingqing8%40AMER.OAUTHAP'
  temp_query_file = './temp_query.txt'
  query_template = 'curl -X GET --header "Authorization: " "https://api.tdameritrade.com/v1/marketdata/quotes?apikey={0}&symbol={1}" > {2}'
  cr = crawler.IntraDayCrawlerTD(FLAGS.data_folder)
  # symbol_list = cr.get_crawl_list_from_three_indices()
  symbol_list = ['AAPL', 'MSFT', 'AMZN', 'ISRG', 'ETSY', 'GOOG']
  symbol_str = ''
  for symbol in symbol_list:
    if symbol_str!='':
      symbol_str += '%2C'
    symbol_str += symbol
  query_message = query_template.format(client_id, symbol_str, temp_query_file)
  print query_message
  os.system(query_message)

def test_update_refresh_time():
  cr = crawler.IntraDayCrawlerTD(FLAGS.data_folder)
  # cr = crawler.IntraDayCrawler(FLAGS.data_folder)
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
  get_multiple_quotes()
  
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
