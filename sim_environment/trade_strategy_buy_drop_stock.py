import simulation_pb2
import trade_strategy
import util.datetime_util as date_time_util

class BuyDropStockTradeStrategy(trade_strategy.TradeStrategy):
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
        self.meet_drop_dict_
          [symbol] = one_time_data # for symbol already meet conditions, we need to update for further analysis

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
        buy_amount = int \
          ((portfolio.get_available_cash() - trade_strategy.k_commission_fee) / self.num_available_slot_ / one_time_data.open)
        transaction = simulation_pb2.Transaction()
        transaction.type = simulation_pb2.Transaction.BUY
        transaction.symbol = symbol
        transaction.amount = buy_amount
        transaction.commission_fee = trade_strategy.k_commission_fee
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
        transaction = simulation_pb2.Transaction()
        transaction.type = simulation_pb2.Transaction.SELL
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
