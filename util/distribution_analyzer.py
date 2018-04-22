import os, sys
import matplotlib.pyplot as plt

import util.display_util as display_util
import proto.stock_pb2 as stock_pb2
import util.datetime_util as datetime_util

class DistributionAnalyzer():
  def __init__(self, title, bin_size):
    self.title_ = title
    
    # The histogram bin size of the relative price change of stocks. 0.001 means 0.1%
    self.bin_size_ = bin_size
    
    self.data_list_ = []

  def __add_one_price_change(self, price_change):
    self.data_list_.append(price_change)

  def add_one_stock_for_distribution(self, symbol, one_stock_data):
    if not self.stock_meet_condition(symbol, one_stock_data):
      return False
    
    result, price_change = self.get_relative_price_change(symbol, one_stock_data)
    if not result:
      print('Failed to get price change for symbol {0} on day {1}'.format(symbol, subfolder))
      return False
    self.__add_one_price_change(price_change)
    return True

  def __prepare_plot(self):
    num_bin = int((max(self.data_list_) - min(self.data_list_)) / self.bin_size_) + 1;
    fig = plt.figure()
    ax = fig.add_subplot(121)
    ax.hist(self.data_list_, bins = num_bin)
    ax.grid()
    ax = fig.add_subplot(122)
    ax.hist(self.data_list_, bins = num_bin, cumulative = 1, label = 'Cumulative')
    ax.grid()
    plt.title(self.title_)

  def plot_distribution(self):
    self.__prepare_plot()
    plt.show()
    plt.clf()

  def export_distribution_to_png(self, img_path):
    self.__prepare_plot()
    plt.savefig(img_path)
    plt.clf()

class OpenCloseDistributionAnalyzer(DistributionAnalyzer):
  def stock_meet_condition(self, symbol, one_stock_data):
    return True

  def get_relative_price_change(self, symbol, one_stock_data):
    if len(one_stock_data.data)<1:
      return False, 0
    open_price = one_stock_data.data[0].open
    last_price = one_stock_data.data[-1].close
    return True, (last_price - open_price) / open_price

class PriceDropAtBeginningDistributionAnalyzer(DistributionAnalyzer):
  def __init__(self, title, bin_size, price_drop_watch_time, drop_threshold):
    DistributionAnalyzer.__init__(self, title, bin_size)
    # when to watch whether there is a price drop. In number of minutes
    self.price_drop_watch_time_ = price_drop_watch_time
    self.drop_threshold_ = drop_threshold
  
  def stock_meet_condition(self, symbol, one_stock_data):
    if len(one_stock_data.data) < 1:
      return False
    
    k_max_allowed_time_diff = 5
    open_time = datetime_util.int_to_time(one_stock_data.data[0].time_val)
    open_price = one_stock_data.data[0].open
    index = 1
    
    min_price = open_price
    last_time_diff = 0
    while (True):
      cur_time = datetime_util.int_to_time(one_stock_data.data[index].time_val)
      time_diff = (cur_time.hour - open_time.hour) * 60 + (cur_time.minute - open_time.minute)
      if time_diff > self.price_drop_watch_time_:
        break
      last_time_diff = time_diff
      min_price = min(min_price, one_stock_data.data[index].low)
      index += 1
      if index >= len(one_stock_data.data):
        return False
    if last_time_diff == 0:
      return False
  
    if self.price_drop_watch_time_ - last_time_diff > k_max_allowed_time_diff:
      return False
    
    self.watch_index_ = index
    self.watch_time_price_ = one_stock_data.data[index].close

    return (min_price - open_price)/open_price < self.drop_threshold_

  def get_relative_price_change(self, symbol, one_stock_data):
    index = self.watch_index_ + 1
    highest_price = self.watch_time_price_
    while index < len(one_stock_data.data):
      highest_price = max(highest_price, one_stock_data.data[index].high)
      index += 1
    price_change = (highest_price - self.watch_time_price_) / self.watch_time_price_
    
    return True, price_change

class PriceDropAtBeginningClosePriceAsChangeDistributionAnalyzer(PriceDropAtBeginningDistributionAnalyzer):
  def get_relative_price_change(self, symbol, one_stock_data):
    price_change = (one_stock_data.data[-1].close - self.watch_time_price_) / self.watch_time_price_
    
    return True, price_change

