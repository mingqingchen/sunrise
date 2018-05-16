import argparse
import os
import sys
import tensorflow as tf

import matplotlib.pyplot as plt

import os, sys
import util.display_util as display_util
import proto.stock_pb2 as stock_pb2
import util.datetime_util as datetime_util

k_eligible_file_name = 'eligible_list.txt'

class DataProvider:
  def __init__(self, root_folder, use_eligible_list = True):
    self.root_folder_ = root_folder
    all_folders = [f for f in os.listdir(self.root_folder_) if os.path.isdir(os.path.join(self.root_folder_, f))]
    self.subfolder_list_ = []
    for subfolder in all_folders:
      if not str.isdigit(subfolder):
        continue
      if len(subfolder)!=8:
        continue
      self.subfolder_list_.append(subfolder)
    self.subfolder_list_.sort()
    self.cur_date_val_ = 0
    self.one_day_data_ = dict()
    self.symbol_timeslot_index_ = dict()
    self.use_eligible_list_ = use_eligible_list
    if use_eligible_list:
      if self.import_eligible_list():
        print('Successfully loaded eligible list. Number of eligible symbols: {0}'.format(len(self.eligible_list_)))
      else:
        print('Failed to load eligible list. Something is wrong!!!')

  def __get_day_folder(self, date_int_val):
    return os.path.join(self.root_folder_, str(date_int_val) + '/')

  def import_eligible_list(self):
    try:
      list_file = os.path.join(self.root_folder_, k_eligible_file_name)
      fid = open(list_file)
      lines = fid.readlines()
      fid.close()
      self.eligible_list_ = dict()
      for line in lines:
        line = line.replace('\n', '')
        if line!='':
          self.eligible_list_[line] = True
    except ValueError:
      return False
    return True

  def __is_eligible(self, symbol):
    if symbol not in self.one_day_data_:
      return False
    total_daily_cash_flow_threshold = 20000 * 6.5 * 60
    min_price_threshold = 5.0

    start_time = 630
    finish_time = 1300
    total_time_point = 390
    fill_in_ratio = 0.8

    total_cash_flow = 0
    num_valid_time_points = 0
    for one_time_data in self.one_day_data_[symbol].data:
      if one_time_data.low < min_price_threshold:
        return False
      if one_time_data.time_val >= start_time and one_time_data.time_val <= finish_time:
        num_valid_time_points += 1
      total_cash_flow += one_time_data.volume * one_time_data.open
    if total_cash_flow < total_daily_cash_flow_threshold:
      return False

    return num_valid_time_points > fill_in_ratio * total_time_point

  def generate_eligible_list(self):
    self.eligible_list_ = dict()
    for symbol in self.one_day_data_:
      if self.__is_eligible(symbol):
        self.eligible_list_[symbol] = True
    list_file = os.path.join(self.root_folder_, k_eligible_file_name)
    fid = open(list_file, 'w')
    for symbol in self.eligible_list_:
      fid.write('{0}\n'.format(symbol))
    fid.close()

  def next_record_day(self, input_day_val):
    num_days = len(self.subfolder_list_)
    for i in range(num_days):
      if self.subfolder_list_[i] == str(input_day_val):
        if i < num_days - 1:
          return True, int(self.subfolder_list_[i + 1])
    return False, 0

  def serialize_one_symbol(self, date_int_val, symbol, one_stock_data):
    intra_day_folder = self.__get_day_folder(date_int_val)
    file_path = os.path.join(intra_day_folder, symbol + '.pb')
    fid = open(file_path, 'w')
    fid.write(one_stock_data.SerializeToString())
    fid.close()

  def load_one_symbol(self, date_int_val, symbol):
    result, one_stock_data = self.deserialize_one_symbol(date_int_val, symbol)
    if not result:
      return False
    self.one_day_data_[symbol] = one_stock_data
    return True

  def get_available_symbol_list(self):
    if self.use_eligible_list_:
      available_list = []
      for symbol in self.one_day_data_.keys():
        if symbol in self.eligible_list_:
          available_list.append(symbol)
      return available_list
    else:
      return self.one_day_data_.keys()

  def get_one_symbol_data(self, symbol):
    return self.one_day_data_[symbol]

  def load_one_day_data(self, date_int_val):
    self.symbol_list_ = self.get_symbol_list_for_a_day(date_int_val)
    self.one_day_data_.clear()
    for symbol in self.symbol_list_:
      if self.use_eligible_list_:
        if symbol in self.eligible_list_:
          self.load_one_symbol(date_int_val, symbol)
      else:
        self.load_one_symbol(date_int_val, symbol)
      
  def has_symbol(self, symbol):
    if self.use_eligible_list_:
      return (symbol in self.one_day_data_) and (symbol in self.eligible_list_)
    else:
      return symbol in self.one_day_data_

  def clear_symbol_index(self):
    self.symbol_timeslot_index_.clear()

  def get_symbol_minute_index(self, symbol, time_int_val):
    """ Given a symbol and its time_int_val, return the index
    :param symbol: symbol name
    :param time_int_val: time int value
    :return: result, index
    """
    index = 0
    if symbol in self.symbol_timeslot_index_:
      index = self.symbol_timeslot_index_[symbol]
    while (index < len(self.one_day_data_[symbol].data)):
      cur_time_val = self.one_day_data_[symbol].data[index].time_val
      if cur_time_val == time_int_val:
        self.symbol_timeslot_index_[symbol] = index
        return 0, index
      elif cur_time_val > time_int_val:
        # this means the required time_int_val has missing value
        return 1, index - 1
      index += 1
    # this means that the required time_int_val never reaches
    return 2, index - 1


  def get_symbol_minute_data(self, symbol, time_int_val):
    """ Get symbol minute data.
        Returns:
          result: 0 for exact match time_int_val, 1 for time_int_val larger than this, 2 for never reaches
          one time slot data
    """
    result, index = self.get_symbol_minute_index(symbol, time_int_val)
    if index < 0:
      return 2, stock_pb2.OneTimeSlotData()
    else:
      return result, self.one_day_data_[symbol].data[index]

  def deserialize_one_symbol(self, date_int_val, symbol):
    intra_day_folder = self.__get_day_folder(date_int_val)
    file_path = os.path.join(intra_day_folder, symbol + '.pb')
    one_stock_data = stock_pb2.OneIntraDayData()
    if not os.path.isfile(file_path):
      return False, one_stock_data
    try:
      fid = open(file_path)
      content = fid.read()
      fid.close()
      one_stock_data.ParseFromString(content)
      return True, one_stock_data
    except ValueError:
      return False, one_stock_data

  def get_all_available_subfolder(self):
    return self.subfolder_list_

  def get_symbol_list_for_a_day(self, date_int_val):
    day_folder = self.__get_day_folder(date_int_val)
    all_files = [f for f in os.listdir(day_folder) if os.path.isfile(os.path.join(day_folder, f)) and f.endswith('.pb')]
    symbol_list = []
    for filename in all_files:
      filename = filename.replace(' ', '')
      filename = filename.replace('.pb', '')
      if self.use_eligible_list_:
        if filename in self.eligible_list_:
          symbol_list.append(filename)
      else:
        symbol_list.append(filename)
    return symbol_list

  def __prepare_one_stock_data_list(self, one_stock_data):
    time_list, open_list, close_list, high_list, low_list = [], [], [], [], []
    for one_slot_data in one_stock_data.data:
      time_list.append(datetime_util.int_to_time(one_slot_data.time_val))
      open_list.append(one_slot_data.open)
      close_list.append(one_slot_data.close)
      high_list.append(one_slot_data.high)
      low_list.append(one_slot_data.low)
    return time_list, open_list, close_list, high_list, low_list

  def __prepare_display_one_symbol_one_day(self, symbol, one_stock_data, transactions):
    time_list, open_list, close_list, high_list, low_list = self.__prepare_one_stock_data_list(one_stock_data)
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

  def diplay_one_symbol_one_day(self, symbol, one_stock_data, transactions = []):
    self.__prepare_display_one_symbol_one_day(symbol, one_stock_data, transactions)
    plt.show()

  def export_one_symbol_one_day(self, symbol, one_stock_data, img_path, transactions = []):
    self.__prepare_display_one_symbol_one_day(symbol, one_stock_data, transactions)
    plt.savefig(img_path)
    plt.clf()

  def batch_output_one_day_data_to_png(self, day_int_val, png_folder):
    if not os.path.isdir(png_folder):
      os.makedirs(png_folder)

    symbol_list = self.get_symbol_list_for_a_day(day_int_val)
    # use the following one to get quick look on major stocks:
    symbol_list = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'ISRG', 'TQQQ', 'BGNE', 'ETSY', 'ARII']
    for symbol in symbol_list:
      print('Processing {0}'.format(symbol))
      result, one_stock_data = self.deserialize_one_symbol(day_int_val, symbol)
      if not result:
        print('Not able to deserilize symbol {0}'.format(symbol))
        continue
      png_file_path = os.path.join(png_folder, symbol + '.png')
      self.export_one_symbol_one_day(symbol, one_stock_data, png_file_path)

      print('Start Time: {0}'.format(one_stock_data.data[0].time_val))
      print('End Time: {0}'.format(one_stock_data.data[-1].time_val))
      print('No. TimePoints: {0}'.format(len(one_stock_data.data)))

