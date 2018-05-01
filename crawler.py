#!/usr/bin/env python 
"""
Retrieve intraday stock data from Google Finance.
"""

import csv
import datetime
import re
import urllib
import argparse
import os
import shutil
import sys
import pandas as pd
import requests
import tensorflow as tf

import os, sys
import json
import util.datetime_util as datetime_util
import proto.stock_pb2 as stock_pb2
import live_trade.trade_api as trade_api

k_intra_day_folder = 'intra_day/'
k_data_folder = './data/'
k_index_list = {'NASDAQ', 'NYSE', 'AMEX'}

class IntraDayCrawler:
  def __init__(self, data_folder):
    self.data_folder_ = data_folder
    self.overwrite_ = False
    self.index_list_url_template = 'https://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange={0}&render=download'
    self.min_num_time_slot_threshold_ = 1
    
    
  def crawl_one_symbol(self, ticker):
    """
    Retrieve intraday stock data from Google Finance.
    Parameters
    ----------
    ticker : str
        Company ticker symbol.
    period : int
        Interval between stock values in seconds.
    days : int
        Number of days of data to retrieve.
    Returns
    -------
    df : pandas.DataFrame
        DataFrame containing the opening price, high price, low price,
        closing price, and volume. The index contains the times associated with
        the retrieved price values.
    """

    period = 1
    days = 1
    uri = 'http://www.google.com/finance/getprices' \
          '?i={period}&p={days}d&f=d,o,h,l,c,v&df=cpct&q={ticker}'.format(ticker=ticker,
                                                                          period=period,
                                                                          days=days)
    page = requests.get(uri)
    reader = csv.reader(page.content.splitlines())
    columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    rows = []
    times = []

    today_date_int_val = datetime_util.get_today()
    one_day_data = stock_pb2.OneIntraDayData()
    one_day_data.symbol = ticker
    one_day_data.date = today_date_int_val
    one_day_data.resolution = period

    for row in reader:
      if len(row)>0:
        if re.match('^[a\d]', row[0]):
            if row[0].startswith('a'):
                start = datetime.datetime.fromtimestamp(int(row[0][1:]))
                cur_time = start
            else:
                cur_time = start+datetime.timedelta(seconds=period*int(row[0]))
            
            times.append(cur_time)
            rows.append(map(float, row[1:]))
            
            one_time_slot_data = one_day_data.data.add()
            one_time_slot_data.time_val = cur_time.hour * 100 + cur_time.minute
            one_time_slot_data.close = float(row[1])
            one_time_slot_data.high = float(row[2])
            one_time_slot_data.low = float(row[3])
            one_time_slot_data.open = float(row[4])
            one_time_slot_data.volume = int(row[5])

    if len(one_day_data.data) < self.min_num_time_slot_threshold_:
      return False, one_day_data
    return True, one_day_data

  def crawl_and_export_one_symbol(self, symbol):
    output_file_path = os.path.join(self.today_folder_, symbol + '.pb')
    if (not self.overwrite_) and os.path.isfile(output_file_path):
      print('Symbol {0} already crawled. Skip.'.format(symbol))
      return True
    print('Crawling: {0}'.format(symbol))
    result, one_day_data = self.crawl_one_symbol(symbol)
    
    if result:
      fid = open(output_file_path, 'w')
      fid.write(one_day_data.SerializeToString())
      fid.close()
      print('Export succesfully!')
      return True
    else:
      print('Crawled content is not useful.')
      return False

  def get_crawl_list_from_three_indices(self):
    symbol_list = []
    for index_name in k_index_list:
      list_file_path = os.path.join(self.data_folder_, index_name + '.csv')
      symbol_data = pd.read_csv(list_file_path)
      for symbol in symbol_data['Symbol']:
        if '^' in symbol or '.' in symbol:
          continue
        symbol = symbol.replace(' ', '')
        symbol_list.append(symbol)
    return symbol_list

  def daily_crawl(self):
    # Make data folder
    if not os.path.exists(self.data_folder_):
      os.makedirs(self.data_folder_)
    
    # Make intra day folder
    intra_day_folder = os.path.join(self.data_folder_, k_intra_day_folder)
    if not os.path.exists(intra_day_folder):
      os.makedirs(intra_day_folder)

    # Make today folder
    today_str = str(datetime_util.get_today()) + '/'
    self.today_folder_ = os.path.join(intra_day_folder, today_str)
    if not os.path.isdir(self.today_folder_):
      os.makedirs(self.today_folder_)

    # First, download index symbol list
    for index_name in k_index_list:
      print('Downloading symbol list for index: {0}'.format(index_name))
      url = self.index_list_url_template.format(index_name)
      temp_filename, headers = urllib.urlretrieve(url)
      local_filename = os.path.join(self.data_folder_, index_name + '.csv')
      if os.path.isfile(local_filename):
        os.remove(local_filename)
      shutil.move(temp_filename, local_filename)

    # Then download intra day price for each symbol
    symbol_list = self.get_crawl_list_from_three_indices()
    for symbol in symbol_list:
      if not self.crawl_and_export_one_symbol(symbol):
        break

class IntraDayCrawlerTD(IntraDayCrawler):
  def __init__(self, data_folder):
    IntraDayCrawler.__init__(self, data_folder)
    self.live_trade_api_ = trade_api.TradeAPI()
    self.live_trade_api_.get_refresh_token()
    self.live_trade_api_.get_new_access_token()
  
  def crawl_one_symbol(self, symbol):
    result, response = self.live_trade_api_.query_historical_price(symbol)
    
    # For the first time, it could be due to expired access token.
    if 'error' in response or (not result):
      self.live_trade_api_.get_new_access_token()
      result, response = self.live_trade_api_.query_historical_price(symbol)
    
    one_symbol_data = stock_pb2.OneIntraDayData()
    if 'error' in response or (not result):
      print ('Could not query symbol {0}. Something is wrong !!!'.format(symbol))
      return False, one_symbol_data
    elif 'candles' not in response:
      print ('Could not find candles in response of symbol {0}. Something is wrong !!!'.format(symbol))
      return False, one_symbol_data
    else:
      one_symbol_data.symbol = symbol
      one_symbol_data.date = datetime_util.get_today()
      one_symbol_data.resolution = 1
    
      for one_time_data_js in response['candles']:
        if 'open' not in one_time_data_js:
          continue
        if 'close' not in one_time_data_js:
          continue
        if 'volume' not in one_time_data_js:
          continue
        if 'high' not in one_time_data_js:
          continue
        if 'low' not in one_time_data_js:
          continue
        if 'datetime' not in one_time_data_js:
          continue
        one_time_data = one_symbol_data.data.add()
        one_time_data.open = float(one_time_data_js['open'])
        one_time_data.close = float(one_time_data_js['close'])
        one_time_data.high = float(one_time_data_js['high'])
        one_time_data.low = float(one_time_data_js['low'])
        one_time_data.volume = int(one_time_data_js['volume'])
        
        cl_time = pd.to_datetime(int(one_time_data_js['datetime']), unit = 'ms')
        cl_time = cl_time.tz_localize('UTC').tz_convert('America/Los_Angeles')
        one_time_data.time_val = cl_time.hour * 100 + cl_time.minute
    if len(one_symbol_data.data) < self.min_num_time_slot_threshold_:
      print('Crawled time slot is too few. Data is considered not useful.')
      # For too few timeslot, we still consider a successful crawl.
      return True, one_symbol_data
    else:
      return True, one_symbol_data

def main(_):
  crawler = IntraDayCrawlerTD(FLAGS.data_folder)
  # crawler = IntraDayCrawler(FLAGS.data_folder)
  crawler.daily_crawl()

if __name__=='__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--data_folder',
    type=str,
    default=k_data_folder,
    help='Root folder for data'
  )
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
