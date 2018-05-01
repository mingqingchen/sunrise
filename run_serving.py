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
k_data_folder_live_trade = './live_trade/'
k_client_id = 'mingqing8%40AMER.OAUTHAP'
k_temp_query_file = './temp_query.txt'

class LiveTrading:
  def __init__(self):
    self.query_template_ = 'curl -X GET --header "Authorization: " "https://api.tdameritrade.com/v1/marketdata/quotes?apikey={0}&symbol={1}" > {2}'
    self.num_symbol_per_request_ = 20
    
    cr = crawler.IntraDayCrawlerTD(FLAGS.data_folder)
    self.symbol_list_ = cr.get_crawl_list_from_three_indices()

    today_int = datetime_util.get_today()

    self.sub_folder_ = os.path.join(k_data_folder_live_trade, str(today_int) + '/')

    if not os.path.isdir(k_data_folder_live_trade):
      os.mkdir(k_data_folder_live_trade)
    if not os.path.isdir(self.sub_folder_):
      os.mkdir(self.sub_folder_)

    self.all_serving_crawled_data_ = dict()
    self.__import_previous_query()

  def __query_once(self, temp_symbol_list):
    symbol_str = ''
    for symbol in temp_symbol_list:
      if symbol_str!='':
        symbol_str += '%2C'
      symbol_str += symbol
    query_message = self.query_template_.format(k_client_id, symbol_str, k_temp_query_file)
    os.system(query_message)
    query_content = json.load(open(k_temp_query_file))

    for symbol in temp_symbol_list:
      if symbol not in query_content:
        continue
      if symbol not in self.all_serving_crawled_data_:
        self.all_serving_crawled_data_[symbol] = stock_pb2.ServingCrawledData()
      self.all_serving_crawled_data_[symbol].symbol = symbol
      one_time_data = self.all_serving_crawled_data_[symbol].data.add()
      one_time_data.time_val = datetime_util.get_cur_time_int()
      """ Current version is just this. Please refer to the following format for future expand.
      {u'divYield': 0.0, u'regularMarketLastPrice': 1.97, u'openPrice': 1.93, u'tradeTimeInLong': 1525132800002, u'lastSize': 200, u'bidPrice': 1.83, u'securityStatus': u'Closed', u'bidId': u'P', u'lastId': u'A', u'shortable': True, u'assetType': u'EQUITY', u'52WkHigh': 6.06, u'quoteTimeInLong': 1525132811065, u'askId': u'P', u'highPrice': 1.97, u'exchange': u'a', u'marginable': True, u'regularMarketTradeTimeInLong': 1525132800002, u'mark': 1.97, u'nAV': 0.0, u'bidTick': u' ', u'regularMarketNetChange': 0.02, u'peRatio': 6.5, u'askPrice': 5.61, u'description': u'Alio Gold Inc. Common Shares (Canada)', u'lastPrice': 1.97, u'askSize': 300, u'symbol': u'ALO', u'delayed': True, u'52WkLow': 1.7, u'bidSize': 1000, u'divAmount': 0.0, u'volatility': 0.22059844, u'digits': 4, u'regularMarketLastSize': 2, u'lowPrice': 1.93, u'divDate': u'', u'closePrice': 1.95, u'exchangeName': u'AMEX', u'netChange': 0.02, u'totalVolume': 42741}
      """
      one_time_data.market_price = query_content[symbol]['regularMarketLastPrice']
      one_time_data.bid_price = query_content[symbol]['bidPrice']

  def __import_previous_query(self):
    all_files = [f for f in os.listdir(self.sub_folder_) if os.path.isfile(os.path.join(self.sub_folder_, f)) and f.endswith('.pb')]
    for file_name in all_files:
      symbol = file_name.replace('.pb', '')
      fid = open(file_path)
      content = fid.read()
      fid.close()
      one_stock_data = stock_pb2.ServingCrawledData()
      one_stock_data.ParseFromString(content)
      self.all_serving_crawled_data_[symbol] = one_stock_data

  def __export_current_query(self):
    for symbol in self.all_serving_crawled_data_:
      file_path = os.path.join(self.sub_folder_, symbol + '.pb')
      fid = open(file_path, 'w')
      fid.write(self.all_serving_crawled_data_[symbol].SerializeToString())
      fid.close()

  def __crawl_one_round(self):
    temp_symbol_list = dict()
    for symbol in self.symbol_list_:
      temp_symbol_list[symbol] = True
      if len(temp_symbol_list) == self.num_symbol_per_request_:
        self.__query_once(temp_symbol_list)
        temp_symbol_list.clear()

  def crawl_forever(self):
    while True:
      self.__crawl_one_round()
      self.__export_current_query()



def test_update_refresh_time():
  """ Test refresh time from Google finance. """
  cr = crawler.IntraDayCrawler(FLAGS.data_folder)
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
  live_trading = LiveTrading()
  live_trading.crawl_forever()
  
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
