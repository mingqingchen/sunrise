import os, sys
import portfolio
import proto.stock_pb2 as stock_pb2
import util.datetime_util as datetime_util

k_commission_fee = 7.0

class TradeStrategy:
  """ Intra-day trading strategy. """
  def run_minute_trade_strategy(self, data_manager, cur_time, portfolio):
    return []

  def update_date(self, date_int_val, data_manager):
    """ This provides needed operations when a new day is updated. """
    self.date_int_val_ = date_int_val
    return

class BuyAndHoldOneStockTradeStrategy(TradeStrategy):
  """ Trade strategy of buying one stock and hold forever. """
  def __init__(self, name):
    self.symbol_ = name
    self.index_ = 0

  def update_date(self, date_int_val, data_manager):
    """ This provides needed operations when a new day is updated.
        For buy and hold one stock strategy, we just need to deserialize one stock
    """
    self.date_int_val_ = date_int_val
    data_manager.load_one_symbol(date_int_val, self.symbol_)
    self.index_ = 0
    return
  
  def run_minute_trade_strategy(self, data_manager, cur_time, portfolio):
    transactions = []
    
    available_cash = portfolio.get_available_cash()
    transaction = stock_pb2.Transaction()
    
    # Try to check whether cur_time is in the recording
    # It is possible that cur_time is not in the recording, since the data is not perfect
    # If it is not in the recording, just returns
    index = data_manager.symbol_minute_index(self.symbol_, cur_time, self.index_)
    if index < 0:
      return []
    
    one_time_data = data_manager.get_one_time_slot_data(self.symbol_, index)
    self.index_ = index
  
    buy_amount = int((available_cash - k_commission_fee)/one_time_data.open)
    if buy_amount <= 0:
      return []
    
    transaction.type = stock_pb2.Transaction.BUY
    transaction.symbol = self.symbol_
    transaction.amount = buy_amount
    transaction.commission_fee = k_commission_fee
    transaction.price = one_time_data.open
    transaction.date = self.date_int_val_
    transaction.time = cur_time

    print transaction

    if portfolio.buy_stock(transaction):
      transactions.append(transaction)

    return transactions

class BuyAndSellOneStockEODTradeStrategy(BuyAndHoldOneStockTradeStrategy):
  """ Trade strategy of buying one stock and sell it at EOD. """
  def run_minute_trade_strategy(self, data_manager, cur_time, portfolio):
    k_eod_time_threshold = 1255
    
    if cur_time < k_eod_time_threshold:
      return BuyAndHoldOneStockTradeStrategy.run_minute_trade_strategy(self, data_manager, cur_time, portfolio)

    # This means the stock is already sold
    if self.symbol_ not in portfolio.get_current_hold_symbol_list():
      return []
    
    index = data_manager.symbol_minute_index(self.symbol_, cur_time, self.index_)
    if index < 0:
      return []
    
    one_time_data = data_manager.get_one_time_slot_data(self.symbol_, index)
    self.index_ = index
    
    transaction = stock_pb2.Transaction()
    transaction.type = stock_pb2.Transaction.SELL
    transaction.symbol = self.symbol_
    transaction.amount = portfolio.get_num_holding(self.symbol_) # means sell all
    transaction.commission_fee = k_commission_fee
    transaction.price = one_time_data.open
    transaction.date = self.date_int_val_
    transaction.time = cur_time

    transactions = []
    if portfolio.sell_stock(transaction):
      transactions.append(transaction)

    return transactions


class BuyDropStockTradeStrategy(TradeStrategy):
  """ Trade strategy of buying top drop stock some time after market open. """
  def __init__(self, watch_time, drop_threshold, watch_time_drop_threshold, rebound_sell_threshold, num_slot):
    # only after watch_time, we can buy any stocks
    self.watch_time_ = watch_time
    
    # We only consider stocks that once drop below this threshold
    self.drop_threshold_ = drop_threshold
    
    # We only buy stocks that meet drop_threhsold within watch_time, and watch_time_drop_threshold after watch time
    self.watch_time_drop_threshold_ = watch_time_drop_threshold
    
    # number of slots that we arrange to buy stocks
    self.num_slot_ = num_slot
    
    # current available slot
    self.num_available_slot_ = self.num_slot_
    
    # a stock will be sold if rebound threshold is hit
    self.rebound_sell_threshold_ = rebound_sell_threshold
    
    # time slot index map for faster array access
    self.symbol_index_map_ = dict()
    
    # map from symbols that meet drop threshold to their time slot data
    self.meet_drop_dict_ = dict()

  def update_date(self, date_int_val, data_manager):
    """ This provides needed operations when a new day is updated.
        For BuyDropStockTradeStrategy, we need to deserialize all stocks
    """
    self.date_int_val_ = date_int_val
    print('Loading all data for day {0}'.format(date_int_val))
    data_manager.load_one_day_data(date_int_val)
    self.symbol_index_map_.clear()
    self.meet_drop_dict_.clear()
    return
  
  
  def run_minute_trade_strategy(self, data_manager, cur_time, portfolio):
    k_market_start_time = 630
    k_sell_all_time = 1255
    watch_time_threshold = datetime_util.add_minute_to_time(k_market_start_time, self.watch_time_)
    
    # First let's see whether there is any stock that meet drop criteria
    for symbol in data_manager.get_available_symbol_list():
      if symbol not in self.symbol_index_map_:
        self.symbol_index_map_[symbol] = 0
      start_index = self.symbol_index_map_[symbol]
      index = data_manager.symbol_minute_index(symbol, cur_time, start_index)
      if index < 0:
        continue  # no time point for this symbol, just continue
      self.symbol_index_map_[symbol] = index
    
      open_price = data_manager.get_one_time_slot_data(symbol, 0).open
      one_time_data = data_manager.get_one_time_slot_data(symbol, index)
      if (one_time_data.low - open_price) / open_price < self.drop_threshold_:
        self.meet_drop_dict_[symbol] = one_time_data
  
      if symbol in self.meet_drop_dict_:
        self.meet_drop_dict_[symbol] = one_time_data # for symbol already meet conditions, we need to update for further analysis
  
    if cur_time < watch_time_threshold:
      return [] # time not ready to buy or sell any stocks

    transactions = []

    # From the drop criteria, find out stock that meets buy criteria, then take buy transaction
    for symbol in self.meet_drop_dict_:
      if self.num_available_slot_ <= 0:
        break
      
      one_time_data = self.meet_drop_dict_[symbol]
      open_price = data_manager.get_one_time_slot_data(symbol, 0).open
      if one_time_data.time_val != cur_time: # for missing data just ignore.
        continue
    
      if cur_time >= k_sell_all_time:
        continue
      if (one_time_data.open - open_price) / open_price < self.watch_time_drop_threshold_:
        buy_amount = int((portfolio.get_available_cash() - k_commission_fee) / self.num_available_slot_ / one_time_data.open)
        transaction = stock_pb2.Transaction()
        transaction.type = stock_pb2.Transaction.BUY
        transaction.symbol = symbol
        transaction.amount = buy_amount
        transaction.commission_fee = k_commission_fee
        transaction.price = one_time_data.open
        transaction.date = self.date_int_val_
        transaction.time = cur_time

        if portfolio.buy_stock(transaction):
          transactions.append(transaction)
          self.num_available_slot_ -= 1
    
    for symbol in portfolio.get_current_hold_symbol_list():
      one_time_data = self.meet_drop_dict_[symbol]
      buy_price = portfolio.get_buy_price(symbol)
      if (one_time_data.open - buy_price) / buy_price > self.rebound_sell_threshold_ or cur_time >= k_sell_all_time:
        transaction = stock_pb2.Transaction()
        transaction.type = stock_pb2.Transaction.SELL
        transaction.symbol = symbol
        transaction.amount = portfolio.get_num_holding(symbol)
        transaction.commission_fee = k_commission_fee
        transaction.price = one_time_data.open
        transaction.date = self.date_int_val_
        transaction.time = cur_time

        if portfolio.sell_stock(transaction):
          transactions.append(transaction)
          self.num_available_slot_ += 1

    return transactions
