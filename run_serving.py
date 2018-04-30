import argparse
import os
import sys
import tensorflow as tf
import json

import crawler
import util.datetime_util as datetime_util
import util.data_provider as data_provider
import proto.stock_pb2 as stock_pb2

FLAGS=None
k_data_folder = './data/'

def get_multiple_quotes():
  client_id = 'mingqing8%40AMER.OAUTHAP'
  temp_query_file = './temp_query.txt'
  query_template = 'curl -X GET --header "Authorization: " "https://api.tdameritrade.com/v1/marketdata/quotes?apikey={0}&symbol={1}" > {2}'

  num_symbol_per_request = 20

  cr = crawler.IntraDayCrawlerTD(FLAGS.data_folder)
  symbol_list = cr.get_crawl_list_from_three_indices()
  # symbol_list = ['AAPL', 'MSFT', 'AMZN', 'ISRG', 'ETSY', 'GOOG']
  
  print('Number of all symbols: {0}'.format(len(symbol_list)))

  all_serving_crawled_data = dict()

  start_index = 0
  while True:
    symbol_str = ''
    temp_symbol_list = dict()
    end_index = min(start_index + num_symbol_per_request, len(symbol_list))
    for i in range(start_index, end_index):
      symbol = symbol_list[i]
      if symbol_str!='':
        symbol_str += '%2C'
      symbol_str += symbol
      temp_symbol_list[symbol] = True
    
    start_index = end_index 
    if end_index == len(symbol_list):
      start_index = 0

    query_message = query_template.format(client_id, symbol_str, temp_query_file)
    print query_message
    os.system(query_message)
    query_content = json.load(open(temp_query_file))

    for symbol in temp_symbol_list:
      if symbol not in query_content:
        continue
      if symbol not in all_serving_crawled_data:
        all_serving_crawled_data[symbol] = stock_pb2.ServingCrawledData()
      all_serving_crawled_data[symbol].symbol = symbol
      one_time_data = all_serving_crawled_data[symbol].data.add()
      one_time_data.time_val = datetime_util.get_cur_time_int()
      one_time_data.market_price = query_content[symbol]['regularMarketLastPrice']
      one_time_data.bid_price = query_content[symbol]['bidPrice']

      if len(all_serving_crawled_data[symbol].data) > 1:
        print all_serving_crawled_data[symbol]
    
    print len(all_serving_crawled_data)

    
  #print query_content['AMZN']

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
