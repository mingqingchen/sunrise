#!/usr/bin/env python 
"""
Retrieve stock data from TD Ameritrade.
For 10 day minute-level query, run
  crawler.py --data_folder=data/daily_data --period=10 --period_type=daily --frequency_type=minute
For 1 year daily-level query, run
  crawler.py --data_folder=data/daily_data --period=1 --period_type=year --frequency_type=daily
"""

import csv
import datetime
import re
import urllib
import argparse
import shutil
import pandas as pd
import requests
import tensorflow as tf
import time

import os, sys
import util.stock_pb2 as stock_pb2
import live_trade.trade_api as trade_api

k_data_folder = './data/minute_data'
k_index_list = {'NASDAQ', 'NYSE', 'AMEX'}

class IntraDayCrawler:
  def __init__(self, data_folder):
    self.data_folder_ = data_folder
    self.overwrite_ = False
    self.index_list_url_template = 'https://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange={0}&render=download'
    self.min_num_time_slot_threshold_ = 1
    
    
  def crawl_one_symbol(self, ticker, period=1, num_days=1):
    """Retrieve intraday stock data from TD ameritrade API.
    Args:
      ticker : Company symbol string.
      period : Interval between stock values in minutes.
      days : Number of days of data to retrieve.
    Returns
      dict : a dict maps from date integer to OneIntraDayData
    """
    uri = 'http://www.google.com/finance/getprices' \
          '?i={period}&p={days}d&f=d,o,h,l,c,v&df=cpct&q={ticker}'.format(ticker=ticker,
                                                                          period=period,
                                                                          days=days)
    page = requests.get(uri)
    reader = csv.reader(page.content.splitlines())
    rows = []
    times = []

    result = {}

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
            date_val = cur_time.year * 10000 + cur_time.month * 100 + cur_time.day

            if date_val not in result:
              one_day_data = stock_pb2.OneIntraDayData()
              one_day_data.symbol = ticker
              one_day_data.date = date_val
              one_day_data.resolution = period
              result[date_val] = one_day_data
            one_time_slot_data = result[date_val].data.add()

            one_time_slot_data.time_val = cur_time.hour * 100 + cur_time.minute
            one_time_slot_data.close = float(row[1])
            one_time_slot_data.high = float(row[2])
            one_time_slot_data.low = float(row[3])
            one_time_slot_data.open = float(row[4])
            one_time_slot_data.volume = int(row[5])

    return result

  def crawl_and_export_one_symbol(self, symbol):
    crawl_result, result = self.crawl_one_symbol(symbol, FLAGS.period, FLAGS.period_type, FLAGS.frequency_type)
    if not crawl_result:
      return Fals

    for day in result:
      day_folder = os.path.join(FLAGS.data_folder, str(day))
      if not os.path.isdir(day_folder):
        os.makedirs(day_folder)

      output_file_path = os.path.join(day_folder, symbol + '.pb')
      fid = open(output_file_path, 'w')
      fid.write(result[day].SerializeToString())
      fid.close()
      print('Export %s succesfully to day %d.' % (symbol, day))
    return True

  def get_crawl_list_from_three_indices(self):
    symbol_list = []
    for index_name in k_index_list:
      list_file_path = os.path.join(FLAGS.data_folder, index_name + '.csv')
      symbol_data = pd.read_csv(list_file_path)
      for symbol in symbol_data['Symbol']:
        if '^' in symbol or '.' in symbol:
          continue
        symbol = symbol.replace(' ', '')
        symbol_list.append(symbol)
    return symbol_list

  def daily_crawl(self, crawl_symbol_list=False):
    # Make data folder
    if not os.path.exists(FLAGS.data_folder):
      os.makedirs(FLAGS.data_folder)

    # First, download index symbol list
    if crawl_symbol_list:
      for index_name in k_index_list:
        print('Downloading symbol list for index: {0}'.format(index_name))
        url = self.index_list_url_template.format(index_name)
        temp_filename, headers = urllib.urlretrieve(url)
        local_filename = os.path.join(FLAGS.data_folder, index_name + '.csv')
        if os.path.isfile(local_filename):
          os.remove(local_filename)
        shutil.move(temp_filename, local_filename)

    # Then download intra day price for each symbol
    symbol_list = self.get_crawl_list_from_three_indices()
    for symbol in symbol_list:
      if not self.crawl_and_export_one_symbol(symbol):
        continue

class IntraDayCrawlerTD(IntraDayCrawler):
  def __init__(self, data_folder):
    IntraDayCrawler.__init__(self, data_folder)
    self.live_trade_api_ = trade_api.TradeAPI()
    self.live_trade_api_.get_refresh_token()
    self.live_trade_api_.get_new_access_token()
  
  def crawl_one_symbol(self, symbol, period=1, period_type='day', frequency_type='minute'):
    result, response = self.live_trade_api_.query_data(symbol, period, period_type, frequency_type)
    
    # For the first time, it could be due to expired access token.
    if 'error' in response or (not result):
      self.live_trade_api_.get_new_access_token()
      result, response = self.live_trade_api_.query_data(symbol, period, period_type, frequency_type)
    
    while 'error' in response and 'transactions per seconds restriction' in response['error']:
      result, response = self.live_trade_api_.query_data(symbol, period, period_type, frequency_type)
      print('Transaction per seconds restriction reached. Sleep for 1 sec.')
      time.sleep(1)

    if 'error' in response or (not result):
      print ('Could not query symbol {0}. Something is wrong !!!'.format(symbol))
      return False, {}
    elif 'candles' not in response:
      print ('Could not find candles in response of symbol {0}. Something is wrong !!!'.format(symbol))
      return False, {}
    else:
      result = {}
      for one_time_data_js in response['candles']:
        cl_time = pd.to_datetime(int(one_time_data_js['datetime']), unit='ms')
        cl_time = cl_time.tz_localize('UTC').tz_convert('America/Los_Angeles')
        if frequency_type == 'minute':
          date_val = cl_time.year * 10000 + cl_time.month * 100 +cl_time.day
        else:
          date_val = cl_time.year
        if date_val not in result:
          one_symbol_data = stock_pb2.OneIntraDayData()
          one_symbol_data.symbol = symbol
          one_symbol_data.date = date_val
          one_symbol_data.resolution = 1
          result[date_val] = one_symbol_data

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

        one_time_data = result[date_val].data.add()
        one_time_data.open = float(one_time_data_js['open'])
        one_time_data.close = float(one_time_data_js['close'])
        one_time_data.high = float(one_time_data_js['high'])
        one_time_data.low = float(one_time_data_js['low'])
        one_time_data.volume = int(one_time_data_js['volume'])

        if frequency_type == 'minute':
          one_time_data.time_val = cl_time.hour * 100 + cl_time.minute
        else:
          one_time_data.time_val = cl_time.year * 10000 + cl_time.month * 100 +cl_time.day

      return True, result

def main(_):
  crawler = IntraDayCrawlerTD(FLAGS.data_folder)
  # crawler = IntraDayCrawler(FLAGS.data_folder)

  # set crawl_symbol_list to false to speed up the process, without downloading the symbol list
  crawler.daily_crawl(crawl_symbol_list=True)

if __name__=='__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--data_folder',
    type=str,
    default=k_data_folder,
    help='Root folder for data'
  )
  parser.add_argument(
    '--period',
    type=int,
    default=1,
    help='Period to crawl'
  )
  parser.add_argument(
    '--period_type',
    type=str,
    default='daily',
    help='Period type to crawl'
  )
  parser.add_argument(
    '--frequency_type',
    type=str,
    default='minute',
    help='Frequency type to crawl'
  )
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
