import matplotlib.pyplot as plt
import os, sys

import sim_environment.trade_strategy as trade_strategy
import util.data_provider as data_provider
import util.datetime_util as datetime_util
import sim_environment.portfolio as portfolio

# corresponds to NY time 9:30
k_open_time = 630

# corresponds to NY time 16:00
k_close_time = 1300

class Simulation():
  """ Intra-day trade simulation. """
  def __init__(self, name):
    # Name of this simulation
    self.name_ = name
    self.start_date_ = 20080416
    
    # end_date is included during simulation
    self.end_date_ = 20180420
    self.portfolio_ = portfolio.PortfolioManager()
  
    self.symbol_last_index_ = dict()

  def set_start_date(self, start_date):
    self.start_date_ = start_date
    
  def set_end_date(self, end_date):
    self.end_date_ = end_date
    
  def deposit_fund(self, sum_money):
    self.portfolio_.deposit_money(sum_money)

  def set_trade_strategy(self, trade_strategy):
    self.trade_strategy_ = trade_strategy

  def set_data_manager(self, data_manager):
    self.data_manager_ = data_manager

  def __update_portfolio(self, time_int_val):
    symbol_timeslot_map = dict()
    for symbol in self.portfolio_.get_current_hold_symbol_list():
      if symbol not in self.symbol_last_index_:
        self.symbol_last_index_[symbol] = 0
      index = self.data_manager_.symbol_minute_index(symbol, time_int_val, self.symbol_last_index_[symbol])
      if index < 0:
        continue
      self.symbol_last_index_[symbol] = index
      one_slot_data = self.data_manager_.get_one_time_slot_data(symbol, index)
      symbol_timeslot_map[symbol] = one_slot_data
    self.portfolio_.update_balance(symbol_timeslot_map)

  def run(self):
    cur_day = self.start_date_
    
    self.transactions_ = []
    
    self.date_time_list_ = []
    self.balances_ = []
    
    while cur_day <= self.end_date_:
      self.symbol_last_index_.clear()
      self.trade_strategy_.update_date(cur_day, self.data_manager_)
      cur_time = k_open_time
      while cur_time <= k_close_time:
        # run_minute_trade_strategy should look at historical price before cur_time, and use the open price at cur_time to trade
        # Should return all the transactions occured
        one_minute_transactions = self.trade_strategy_.run_minute_trade_strategy(self.data_manager_, cur_time, self.portfolio_)
      
        # self.portfolio_ should be updated inside this function
        self.__update_portfolio(cur_time)
      
        # record all the transactions
        for transaction in one_minute_transactions:
          self.transactions_.append(transaction)

        # The following lines are just for display for final visualization
        cur_date_time = datetime_util.int_to_datetime(cur_day, cur_time)
        normalized_time = datetime_util.convert_to_normalized_time(cur_date_time, k_open_time, k_close_time)
        self.date_time_list_.append(normalized_time)
        self.balances_.append(self.portfolio_.get_balance())
        
        cur_time = datetime_util.next_minute(cur_time)

      has_next_day, cur_day = self.data_manager_.next_record_day(cur_day)
      if not has_next_day:
        break

  def get_simulation_run_result(self):
    return self.transactions_, self.date_time_list_, self.balances_


