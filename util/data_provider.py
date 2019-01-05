
import matplotlib.pyplot as plt

import os
import stock_pb2

k_eligible_file_name = 'eligible_list.txt'


# Class providing easy access to crawled data
# Note that use_eligible_list is set to true by default, which filters out a lot of stocks based on a whitelist
class DataProvider:
  def __init__(self, root_folder, use_eligible_list=True):
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
      assert self.__import_eligible_list()

  def __get_day_folder(self, date_int_val):
    """Get the absolute folder path for a given input integer day."""
    return os.path.join(self.root_folder_, str(date_int_val) + '/')

  def __import_eligible_list(self):
    """Import eligible list from a text file. Return false if failed to import."""
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

  def get_all_available_dates(self):
    """Return a list of strings containing crawled date in the format of 20181230."""
    return self.subfolder_list_

  def next_record_day(self, input_day_val):
    """For a input day, return the next day with recorded symbols. Assume subfolder_list_ is a sorted integer list.
    
    Args:
       input_day_val: integer of input day
    Returns:
       Integer of the next day. -1 for not available.
    """
    assert len(self.subfolder_list_) > 0
    if input_day_val < int(self.subfolder_list_[0]):
      return int(self.subfolder_list_[0])
    num_days = len(self.subfolder_list_)
    for i in range(num_days):
      if self.subfolder_list_[i] == str(input_day_val):
        if i < num_days - 1:
          return int(self.subfolder_list_[i + 1])
    return -1

  def deserialize_one_symbol(self, date_int_val, symbol):
    """Given an integer date_int_val and symbol, return T/F result of deserialization and one_stock_data."""
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

  def load_one_symbol_data(self, date_int_val, symbol):
    """Given a date_int_val and symbol, deserialize one stock into one_day_data_ from disk.

    Args:
      date_int_val: input integer of given date
      symbol: input string of symbol name
    Returns:
       T/F of whether loading is successful.
    """
    result, one_stock_data = self.deserialize_one_symbol(date_int_val, symbol)
    if not result:
      return False
    self.one_day_data_[symbol] = one_stock_data
    return True

  def get_one_symbol_data(self, symbol):
    return self.one_day_data_[symbol]

  def get_symbol_list_for_a_day(self, date_int_val):
    """Returns a list of symbols that are available in a date_int_val subfolder."""
    day_folder = self.__get_day_folder(date_int_val)
    symbol_list = []
    if not os.path.isdir(day_folder):
      return symbol_list

    all_files = [f for f in os.listdir(day_folder) if os.path.isfile(os.path.join(day_folder, f)) and f.endswith('.pb')]
    for filename in all_files:
      filename = filename.replace(' ', '')
      filename = filename.replace('.pb', '')
      if self.use_eligible_list_:
        if filename in self.eligible_list_:
          symbol_list.append(filename)
      else:
        symbol_list.append(filename)
    return symbol_list

  def load_one_day_data(self, date_int_val):
    """Load one day's available symbol.

    Args:
       date_int_val: integer value of a day, in the format of "20181228"
    """
    self.symbol_list_ = self.get_symbol_list_for_a_day(date_int_val)
    self.one_day_data_.clear()
    for symbol in self.symbol_list_:
      if self.use_eligible_list_:
        if symbol in self.eligible_list_:
          self.load_one_symbol_data(date_int_val, symbol)
      else:
        self.load_one_symbol_data(date_int_val, symbol)

  def get_available_symbol_list(self):
    if self.use_eligible_list_:
      available_list = []
      for symbol in self.one_day_data_.keys():
        if symbol in self.eligible_list_:
          available_list.append(symbol)
      return available_list
    else:
      return self.one_day_data_.keys()

  def clear_symbol_index(self):
    self.symbol_timeslot_index_.clear()

  def get_symbol_minute_index(self, symbol, time_int_val):
    """Given a symbol and its time_int_val, return the index.

    Args:
      symbol: symbol name
      time_int_val: time int value
    Returns:
      result: 0 indicating successful found minute index, 1 for not existing but in the middle of two other timepoints,
              2 indicating not existing and at the end of crawling time
      index: the index associated with the time_int_val
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
    """Get symbol minute data.

    Args:
      symbol: symbol name string
      time_int_val: integer of time point
    Returns:
      result: 0 for exact match time_int_val, 1 for time_int_val larger than this, 2 for never reaches
              one time slot data
    """
    result, index = self.get_symbol_minute_index(symbol, time_int_val)
    if index < 0:
      return 2, stock_pb2.OneTimeSlotData()
    else:
      return result, self.one_day_data_[symbol].data[index]

  # --------------------------- Utility function related to eligible list ---------------------------
  def __is_eligible(self, symbol):
    """Determine if a symbol is eligible based on daily cash flow of current loaded status in one_day_data_[symbol].

    Args:
      symbol: input string of a symbol name
    Returns:
      True or False indicating if the symbol is eligible
    """
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
    """Generate member variable eligible_list_ based on eligibility of each symbol."""
    self.eligible_list_ = dict()
    for symbol in self.one_day_data_:
      if self.__is_eligible(symbol):
        self.eligible_list_[symbol] = True

  def export_eligible_list(self):
    """Export eligible_list_ to a text file."""
    list_file = os.path.join(self.root_folder_, k_eligible_file_name)
    fid = open(list_file, 'w')
    for symbol in self.eligible_list_:
      fid.write('{0}\n'.format(symbol))
    fid.close()