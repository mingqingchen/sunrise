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

import util.datetime_util as datetime_util
import proto.stock_pb2 as stock_pb2

import pdb

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
      return
    print('Crawling: {0}'.format(symbol))
    result, one_day_data = self.crawl_one_symbol(symbol)
    
    if result:
      fid = open(output_file_path, 'w')
      fid.write(one_day_data.SerializeToString())
      fid.close()
      print('Export succesfully!')
    else:
      print('Crawled content is not useful.')

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
    for index_name in k_index_list:
      list_file_path = os.path.join(self.data_folder_, index_name + '.csv')
      symbol_data = pd.read_csv(list_file_path)
      for symbol in symbol_data['Symbol']:
        if '^' in symbol:
          continue
        symbol = symbol.replace(' ', '')
        self.crawl_and_export_one_symbol(symbol)

class IntraDayCrawlerTD(IntraDayCrawler):
  def __init__(self, data_folder):
    IntraDayCrawler.__init__(self, data_folder)
    self.query_template_ = 'https://api.tdameritrade.com/v1/marketdata/{0}/pricehistory?period=1&frequencyType=minute&frequency=1'    
    self.__load_token()
    self.has_token_ = self.__load_token()

  def __load_token(self):
    k_token_file = './token.txt'
    if not os.path.isfile(k_token_file):
      print('Token file does not exist')
      return False
    fid = open('token.txt')
    lines = fid.readlines()
    fid.close()

    self.token_string_ = lines[0]
    self.token_string_ = self.token_string_.replace('\n', '')
    return True

  def crawl_one_symbol(self, symbol):
    local_file_name = './temp.txt'
    query_string = self.token_string_ + ' "' + self.query_template_.format(symbol) + '" > {0}'.format(local_file_name)
    pdb.set_trace()
    os.system(query_string)

    fid = open(local_file_name)
    lines = fid.readlines()
    fid.close()

    one_symbol_data = stock_pb2.OneIntraDayData()
    one_symbol_data.symbol = symbol
    one_symbol_data.date = datetime_util.get_today()
    one_symbol_data.resolution = 1
    for line in lines:
      if '"candles":' in line:
        start_index = line.index('[')
        finish_index = line.index(']')
        line = line[start_index + 1 : finish_index]
        split_lines = line.split('},')   
    
        for timeslot_line in split_lines:
          timeslot_line = timeslot_line.replace('{', '')
          timeslot_line = timeslot_line.replace('}', '')
          split_content = timeslot_line.split(',')
      
          one_time_data = one_symbol_data.data.add()
          for content in split_content:
            kv_pair = content.split(':')
            if len(kv_pair)!=2:
              continue
            str_key = kv_pair[0].replace('"', '')
            str_val = kv_pair[1]
            if str_key == 'open':
              one_time_data.open = float(str_val)
            elif str_key == 'high':
              one_time_data.high = float(str_val)
            elif str_key == 'close':
              one_time_data.close = float(str_val)
            elif str_key == 'low':
              one_time_data.low = float(str_val)
            elif str_key == 'volume':
              one_time_data.volume = int(str_val)
            elif str_key == 'datetime':
              cl_time = pd.to_datetime(int(str_val), unit = 'ms')
              cl_time = cl_time.tz_localize('UTC').tz_convert('America/Los_Angeles')
              one_time_data.time_val = cl_time.hour * 100 + cl_time.minute

    return True, one_symbol_data

def main(_):
  # crawler = IntraDayCrawlerTD(FLAGS.data_folder)
  crawler = IntraDayCrawler(FLAGS.data_folder)
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
