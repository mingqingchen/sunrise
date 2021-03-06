
import os

import datetime_util
import stock_pb2

k_eligible_file_name = 'eligible_list.txt'


def sort_data_based_on_time(input):
  """Sortinput ONeIntraDayData based on time_val.
  Args:
    input: OneIntraDayData
  Returns:
    output: OneIntraDayData with data sorted
  """
  time_data_map = {}
  output = stock_pb2.OneIntraDayData()
  output.symbol = input.symbol
  output.date = input.date
  output.resolution = input.resolution

  for data in input.data:
    time_data_map[data.time_val] = data
  for item in sorted(time_data_map.items(), key=lambda s: s[0]):
    one_time_data = output.data.add()
    one_time_data.CopyFrom(item[1])
  return output


def if_two_float_close(a, b):
  if (a == 0.) and (b == 0.):
    return True
  if abs(a - b) < 0.03:
    return True
  return abs(a - b) / (abs(a) + abs(b)) < 0.01

def is_one_day_a_match(one_day_minute_data, one_day_summary_data, include_pre_after_market):
  """Determine whether one_day_minute_data is a match for one_day_summary_data based on high and low.
  Args:
    one_day_minute_data: a OneIntraDayData
    one_day_summary_data: a OneTimeSlotData
  Returns:
    True or False indicating whether a match
  """
  if len(one_day_minute_data.data) == 0:
    return False
  open_time = 630
  close_time = 1300
  if include_pre_after_market:
    open_time = 0
    close_time = 2359

  is_first = True
  for one_time_data in one_day_minute_data.data:
    if one_time_data.time_val < open_time or one_time_data.time_val > close_time:
      continue
    if is_first:
      max_val, min_val = one_time_data.low, one_time_data.low
      is_first = False
    max_val = max(max_val, one_time_data.high)
    min_val = min(min_val, one_time_data.low)
  if is_first:
    return False
  if not if_two_float_close(one_day_summary_data.high, max_val):
    return False
  if not if_two_float_close(one_day_summary_data.low, min_val):
    return False
  return True


def merge_one_intra_day_data(day_data_a, day_data_b):
  """Merge two OneIntraDayData.
  Args:
    day_data_a: data A
    day_data_b: data B
  Returns:
    result: True or False of merging success or not. The two data must have same symbol, date and resolution
    merged_data: merged result
  """
  merged_data = stock_pb2.OneIntraDayData()
  if day_data_a.symbol != day_data_b.symbol:
    return False, merged_data
  if day_data_a.date != day_data_b.date:
    return False, merged_data
  if day_data_a.resolution != day_data_b.resolution:
    return False, merged_data
  if len(day_data_a.data) == 0:
    return True, day_data_b
  if len(day_data_b.data) == 0:
    return True, day_data_a
  merged_data.symbol = day_data_b.symbol
  merged_data.date = day_data_b.date
  merged_data.resolution = day_data_b.resolution
  index_a, index_b = 0, 0
  while index_a < len(day_data_a.data) and index_b < len(day_data_b.data):
    one_time_data = merged_data.data.add()
    if day_data_a.data[index_a].time_val < day_data_b.data[index_b].time_val:
      one_time_data.CopyFrom(day_data_a.data[index_a])
      index_a += 1
    elif day_data_a.data[index_a].time_val > day_data_b.data[index_b].time_val:
      one_time_data.CopyFrom(day_data_b.data[index_b])
      index_b += 1
    else:
      one_time_data.CopyFrom(day_data_b.data[index_b])
      index_a += 1
      index_b += 1
  if index_a < len(day_data_a.data):
    for index in range(index_a, len(day_data_a.data)):
      one_time_data = merged_data.data.add()
      one_time_data.CopyFrom(day_data_a.data[index])
  elif index_b < len(day_data_b.data):
    for index in range(index_b, len(day_data_b.data)):
      one_time_data = merged_data.data.add()
      one_time_data.CopyFrom(day_data_b.data[index])
  return True, merged_data


# Class providing easy access to crawled data
# Note that use_eligible_list is set to true by default, which filters out a lot of stocks based on a whitelist
class DataProvider:
  def __init__(self, root_folder, use_eligible_list=True):
    self.root_folder_ = root_folder
    all_folders = [f for f in os.listdir(self.root_folder_) if os.path.isdir(os.path.join(self.root_folder_, f))]
    self.subfolder_list_ = []
    self.subfolder_set_ = set()
    for subfolder in all_folders:
      if not str.isdigit(subfolder):
        continue
      if len(subfolder)!=8:
        continue
      self.subfolder_list_.append(subfolder)
      self.subfolder_set_.add(subfolder)
    self.subfolder_list_.sort()
    self.cur_date_val_ = 0
    self.one_day_data_ = dict()
    self.symbol_timeslot_index_ = dict()
    self.use_eligible_list_ = use_eligible_list
    if use_eligible_list:
      self._eligible_dict = {}

  def __get_day_folder(self, date_int_val):
    """Get the absolute folder path for a given input integer day."""
    return os.path.join(self.root_folder_, str(date_int_val) + '/')

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
      if self.subfolder_list_[i] > str(input_day_val):
        return int(self.subfolder_list_[i])
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
    if self.use_eligible_list_:
      if self._is_data_eligible(one_stock_data):
        return False
    self.one_day_data_[symbol] = one_stock_data
    return True

  def is_symbol_available(self, symbol):
    return symbol in self.one_day_data_

  def get_one_symbol_data(self, symbol):
    return self.one_day_data_[symbol]

  def _is_data_eligible(self, one_symbol_data):
    """Determine if a symbol is eligible based on daily cash flow of current loaded status in one_day_data_[symbol].

    Args:
      symbol: input string of a symbol name
    Returns:
      True or False indicating if the symbol is eligible
    """
    k_total_daily_cash_flow_threshold = 20000 * 6.5 * 60
    min_price_threshold = 5.0

    k_start_time = 630
    k_finish_time = 1300
    k_total_time_point = 390
    k_fill_in_ratio = 0.8

    total_cash_flow = 0
    num_valid_time_points = 0
    for one_time_data in one_symbol_data.data:
      if one_time_data.low < min_price_threshold:
        return False
      if k_start_time <= one_time_data.time_val <= k_finish_time:
        num_valid_time_points += 1
      total_cash_flow += one_time_data.volume * one_time_data.open
    if total_cash_flow < k_total_daily_cash_flow_threshold:
      return False

    return num_valid_time_points > k_fill_in_ratio * k_total_time_point
    return True

  def _get_symbol_list_for_a_day_from_disk(self, date_int_val):
    """Returns a list of symbols that are available in a date_int_val subfolder."""
    day_folder = self.__get_day_folder(date_int_val)
    symbol_list = []
    if not os.path.isdir(day_folder):
      return symbol_list

    all_files = [f for f in os.listdir(day_folder) if os.path.isfile(os.path.join(day_folder, f)) and f.endswith('.pb')]
    for filename in all_files:
      filename = filename.replace(' ', '')
      filename = filename.replace('.pb', '')
      symbol_list.append(filename)
    return symbol_list

  def load_one_day_data(self, date_int_val):
    """Load one day's available symbol.

    Args:
       date_int_val: integer value of a day, in the format of "20181228"
    """
    symbol_list = self._get_symbol_list_for_a_day_from_disk(date_int_val)
    self.one_day_data_.clear()
    self.clear_symbol_index()
    for symbol in symbol_list:
      self.load_one_symbol_data(date_int_val, symbol)

  def get_available_symbol_list(self):
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

  def extract_previous_n_timepoints(self, symbol, date_int_val, time_int_val, n):
    """Extract previous n timepoints for a given day and time point.
    Args:
      symbol: symbol name
      date_int_val: integer of day
      time_int_val: integer of time
      n: number of timepoints to extract
    Returns:
      result: T/F indicating whether the extraction is successful
      prev_n_points: A list of OneTimeSlotData that containing those information. Possible to raise error
    """
    prev_n_points = []
    if not self.load_one_symbol_data(date_int_val, symbol):
      return False, prev_n_points
    result, index = self.get_symbol_minute_index(symbol, time_int_val)
    if result == 2:
      return False, prev_n_points
    num_remaining_points = n
    numpoints = index + 1
    for i in range(max(0, numpoints - n), numpoints):
      prev_n_points.append(self.one_day_data_[symbol].data[i])
    num_remaining_points -= len(prev_n_points)

    k_earliest_crawled_time = 20170101   # set up an earliest crawled time
    current_date = date_int_val

    while (num_remaining_points > 0):
      current_date = datetime_util.increment_day(current_date, -1)
      if current_date < k_earliest_crawled_time:
        break
      if str(current_date) not in self.subfolder_set_:
        continue
      if self.load_one_symbol_data(current_date, symbol):
        cur_day_list = []
        num_one_day_points = len(self.one_day_data_[symbol].data)
        numpoints = min(num_remaining_points, num_one_day_points)
        for i in range(num_one_day_points - numpoints, num_one_day_points):
          cur_day_list.append(self.one_day_data_[symbol].data[i])
        prev_n_points = cur_day_list + prev_n_points
        num_remaining_points -= numpoints
    return (len(prev_n_points) == n), prev_n_points

  def extract_previous_timepoints(self, symbol, date_int_val, time_int_val, date_span, time_span):
    """Extract previous timepoints within a time range defined by date_span and time_span.
    Args:
      symbol: symbol name
      date_int_val: integer of day
      time_int_val: integer of time
      date_span: an integer indicating how many days to look backwards
      time_span: an integer indicating how much time to look backwards
    Returns:
      prev_points: A list of OneTimeSlotData that containing previous time points within the time range.
    """
    prev_points = []
    current_date = date_int_val
    while datetime_util.date_diff(current_date, date_int_val) <= date_span:
      if str(current_date) in self.subfolder_set_:
        if self.load_one_symbol_data(current_date, symbol):
          cur_day_list = []
          for one_time_slot_data in self.one_day_data_[symbol].data:
            if datetime_util.date_diff(current_date, date_int_val) < date_span or \
                    datetime_util.minute_diff(one_time_slot_data.time_val, time_int_val) <= time_span:
              cur_day_list.append(one_time_slot_data)
          prev_points = cur_day_list + prev_points
      current_date = datetime_util.increment_day(current_date, -1)
    return prev_points






