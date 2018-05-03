import crawler
import util.datetime_util as datetime_util
import proto.stock_pb2 as stock_pb2
import live_trade.trade_api as trade_api
import os

k_data_folder = './data/'
k_data_folder_live_trade = './live_trade/'
k_temp_query_file = './temp_query.txt'

class LiveTrading:
  def __init__(self):
    self.num_symbol_per_request_ = 20
    
    cr = crawler.IntraDayCrawlerTD(k_data_folder)
    self.symbol_list_ = cr.get_crawl_list_from_three_indices()

    today_int = datetime_util.get_today()

    self.sub_folder_ = os.path.join(k_data_folder_live_trade, str(today_int) + '/')

    if not os.path.isdir(k_data_folder_live_trade):
      os.mkdir(k_data_folder_live_trade)
    if not os.path.isdir(self.sub_folder_):
      os.mkdir(self.sub_folder_)

    self.all_serving_crawled_data_ = dict()
    self.__import_previous_query()
    
    self.instance_ = trade_api.TradeAPI()    

  def __query_once(self, temp_symbol_list):
    result, query_content = self.instance_.query_updated_quotes(temp_symbol_list)
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
      one_time_data.open_price = query_content[symbol]['openPrice']
      one_time_data.total_volume = query_content[symbol]['totalVolume']


  def __import_previous_query(self):
    all_files = [f for f in os.listdir(self.sub_folder_) if os.path.isfile(os.path.join(self.sub_folder_, f)) and f.endswith('.pb')]
    for file_name in all_files:
      symbol = file_name.replace('.pb', '')
      file_path = os.path.join(self.sub_folder_, file_name)
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
    cur_crawled_amount = 0
    for symbol in self.symbol_list_:
      temp_symbol_list[symbol] = True
      if len(temp_symbol_list) == self.num_symbol_per_request_:
        self.__query_once(temp_symbol_list)
        temp_symbol_list.clear()
        cur_crawled_amount += self.num_symbol_per_request_
        print('{0}/{1} has been crawled. '.format(cur_crawled_amount, len(self.symbol_list_)))

  def crawl_forever(self):
    while True:
      self.__crawl_one_round()
      self.__export_current_query()

  def crawl_once(self):
      start = time.time()
      print("start time is: ", start)
      self.__crawl_one_round()
      print("finished, time used is: ", (time.time() - start))
