import proto.stock_pb2 as stock_pb2
import util.datetime_util as datetime_util
import train.model_manager as model_manager
import operator

import tensorflow as tf

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

  def update_date(self, date_int_val, data_manager):
    """ This provides needed operations when a new day is updated.
        For buy and hold one stock strategy, we just need to deserialize one stock
    """
    self.date_int_val_ = date_int_val
    data_manager.load_one_symbol(date_int_val, self.symbol_)
    return
  
  def run_minute_trade_strategy(self, data_manager, cur_time, portfolio):
    transactions = []
    
    available_cash = portfolio.get_available_cash()
    transaction = stock_pb2.Transaction()
    
    # Try to check whether cur_time is in the recording
    # It is possible that cur_time is not in the recording, since the data is not perfect
    # If it is not in the recording, just returns
    result, one_time_data = data_manager.get_symbol_minute_data(self.symbol_, cur_time)
    if result != 0:
      return []
  
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
    
    result, one_time_data = data_manager.get_symbol_minute_data(self.symbol_, cur_time)
    if result != 0:
      return []
    
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
  def __init__(self, params):
    self.params_ = params
    
    self.num_available_slot_ = self.params_.num_slot
    
    # map from symbols that meet drop threshold to their time slot data
    self.meet_drop_dict_ = dict()
  
    # map from symbols to open price
    self.open_price_dict_ = dict()
  
    # black list of symbols that have too few timepoint
    self.too_few_timepoint_blacklist_ = dict()
  
    # mapping from symbol to how many times have bought
    self.buy_time_dict_ = dict()

  def update_date(self, date_int_val, data_manager):
    """ This provides needed operations when a new day is updated.
        For BuyDropStockTradeStrategy, we need to deserialize all stocks
    """
    self.date_int_val_ = date_int_val
    print('Loading all data for day {0}'.format(date_int_val))
    data_manager.load_one_day_data(date_int_val)
    self.meet_drop_dict_.clear()
    self.open_price_dict_.clear()
    self.too_few_timepoint_blacklist_.clear()
    self.buy_time_dict_.clear()
    return
  
  
  def run_minute_trade_strategy(self, data_manager, cur_time, portfolio):
    k_market_start_time = 630
    k_sell_all_time = 1255
    watch_time_threshold = datetime_util.add_minute_to_time(k_market_start_time, self.params_.watch_time)
    
    # First let's see whether there is any stock that meet drop criteria
    for symbol in data_manager.get_available_symbol_list():
      if symbol in self.too_few_timepoint_blacklist_:
        if self.too_few_timepoint_blacklist_[symbol] == True:
          continue
      else:
        one_symbol_data = data_manager.get_one_symbol_data(symbol)
        if (len(one_symbol_data.data) < self.params_.minimal_timepoint):
          self.too_few_timepoint_blacklist_[symbol] = True
          continue
        else:
          self.too_few_timepoint_blacklist_[symbol] = False
      
      if symbol in self.open_price_dict_:
        open_price = self.open_price_dict_[symbol]
      else:
        result, one_time_data = data_manager.get_symbol_minute_data(symbol, k_market_start_time)
        if result == 2:
          continue
        open_price = one_time_data.open
        self.open_price_dict_[symbol] = open_price
      
      if open_price < self.params_.minimal_price:
        continue
      
      result, one_time_data = data_manager.get_symbol_minute_data(symbol, cur_time)
      if (one_time_data.low - open_price) / open_price < self.params_.drop_threshold:
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
    
      if symbol in self.buy_time_dict_:
        if self.buy_time_dict_[symbol] >= self.params_.num_buy_time:
          continue
    
      # We will not increase holded amount for the same stock, to reduce the risk
      if symbol in portfolio.get_current_hold_symbol_list():
        continue
      
      one_time_data = self.meet_drop_dict_[symbol]
      open_price = self.open_price_dict_[symbol]
      if one_time_data.time_val != cur_time: # for missing data just ignore.
        continue
    
      if cur_time >= k_sell_all_time:
        continue
      if (one_time_data.open - open_price) / open_price < self.params_.watch_time_drop_threshold:
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
          if symbol not in self.buy_time_dict_:
            self.buy_time_dict_[symbol] = 0
          self.buy_time_dict_[symbol] += 1
            
    
    for symbol in portfolio.get_current_hold_symbol_list():
      one_time_data = self.meet_drop_dict_[symbol]
      buy_price = portfolio.get_buy_price(symbol)
      increase_ratio = (one_time_data.open - buy_price) / buy_price
      if increase_ratio > self.params_.rebound_sell_threshold or increase_ratio < self.params_.stop_loss_sell_threshold or cur_time >= k_sell_all_time:
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


class BuyBestAIRankedTradeStrategy(TradeStrategy):
  """ Trade strategy of buying top ranked symbols recommended by NN. """
  def __init__(self, sess, model_path):
    self.num_available_slot_ = 5

    self.mm_ = model_manager.FixedNumTimePointsModelManager()
    self.mm_.init_for_serving()

    saver = tf.train.Saver()
    saver.restore(sess, model_path)

    self.buy_score_dict_ = dict()
    self.sell_price_dict_ = dict()

    self.num_eligible_list_requirement_ = 100
    self.increase_check_threshold_ = 0.005

    self.buy_stock_prob_threshold_ = 0.65

  def update_date(self, date_int_val, data_manager):
    """ This provides needed operations when a new day is updated.
        For BuyBestAIRankedTradeStrategy, we need to deserialize all stocks
    """
    self.date_int_val_ = date_int_val
    print('Loading all data for day {0}'.format(date_int_val))
    data_manager.load_one_day_data(date_int_val)
    self.buy_score_dict_.clear()
    self.sell_price_dict_.clear()
    return

  def __sell_one_symbol_completely(self, symbol, cur_time, sell_price, portfolio):
    transaction = stock_pb2.Transaction()
    transaction.type = stock_pb2.Transaction.SELL
    transaction.symbol = symbol
    transaction.amount = portfolio.get_num_holding(symbol)
    transaction.commission_fee = k_commission_fee
    transaction.price = sell_price
    transaction.date = self.date_int_val_
    transaction.time = cur_time

    if portfolio.sell_stock(transaction):
      self.num_available_slot_ += 1
      return True, transaction
    else:
      return False, transaction

  def run_minute_trade_strategy(self, data_manager, cur_time, portfolio):
    k_market_start_time = 630
    k_sell_all_time = 1255

    if cur_time % 10 == 0:
      print('Running simulation at time {0}'.format(cur_time))

    transactions = []

    # First, sell all symbols that trigger the checking price threshold and NN thinks it is time to sell
    for symbol in portfolio.get_current_hold_symbol_list():
      result, one_symbol_minute_data = data_manager.get_symbol_minute_data(symbol, cur_time)
      if result == 2:
        continue

      if cur_time > k_sell_all_time:
        result, transaction = self.__sell_one_symbol_completely(symbol, cur_time, one_symbol_minute_data.open, portfolio)
        if result:
          print transaction
          transactions.append(transaction)
          continue

      buy_price = portfolio.get_buy_price(symbol)
      increase_ratio = (one_symbol_minute_data.open - buy_price) / buy_price

      if increase_ratio > self.increase_check_threshold_:
        result, transaction = self.__sell_one_symbol_completely(symbol, cur_time, one_symbol_minute_data.open,
                                                                  portfolio)
        if result:
          transactions.append(transaction)
          self.sell_price_dict_[symbol] = transaction.price

    if cur_time > k_sell_all_time:
      return transactions

    if self.num_available_slot_ == 0:
      return transactions

    # Then let's see whether there is any stock that has highest score to buy
    for symbol in data_manager.get_available_symbol_list():
      if self.num_available_slot_ == 0:
        break

      one_symbol_data = data_manager.get_one_symbol_data(symbol)
      result, index = data_manager.get_symbol_minute_index(symbol, cur_time)
      if result == 2:
        continue

      if portfolio.if_symbol_is_in_holding(symbol):
        continue

      one_symbol_data = data_manager.get_one_symbol_data(symbol)
      if not self.mm_.is_eligible_to_be_fed_into_network(one_symbol_data, index):
        continue

      prob_score = self.mm_.compute_prob(one_symbol_data, index)
      self.buy_score_dict_[symbol] = prob_score

    if len(self.buy_score_dict_) > self.num_eligible_list_requirement_:
      added_symbols = []
      for symbol, score in sorted(self.buy_score_dict_.iteritems(), key=lambda (k,v): (v,k), reverse=True):
        if self.num_available_slot_ == 0:
          break

        if score < self.buy_stock_prob_threshold_:
          break

        if portfolio.if_symbol_is_in_holding(symbol):
          continue

        result, one_symbol_minute_data = data_manager.get_symbol_minute_data(symbol, cur_time)
        if result == 2:
          continue

        if symbol in self.sell_price_dict_:
          if one_symbol_minute_data.open > self.sell_price_dict_[symbol] - self.increase_check_threshold_:
            continue

        buy_amount = int((portfolio.get_available_cash() - k_commission_fee) /
                         self.num_available_slot_ / one_symbol_minute_data.open)
        transaction = stock_pb2.Transaction()
        transaction.type = stock_pb2.Transaction.BUY
        transaction.symbol = symbol
        transaction.amount = buy_amount
        transaction.commission_fee = k_commission_fee
        transaction.price = one_symbol_minute_data.open
        transaction.date = self.date_int_val_
        transaction.time = cur_time

        if portfolio.buy_stock(transaction):
          transactions.append(transaction)
          self.num_available_slot_ -= 1

    return transactions