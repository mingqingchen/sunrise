import tensorflow as tf

import sim_environment.trade_strategy as trade_strategy
import train.model_manager as model_manager
import proto.stock_pb2 as stock_pb2

class BuyBestAIRankedTradeStrategy(trade_strategy.TradeStrategy):
  """ Trade strategy of buying top ranked symbols recommended by NN. """
  def __init__(self, sess, buy_model_param, sell_model_param):
    self.num_available_slot_ = 5

    buy_variables, sell_variables = [], []

    self.mm_buy_ = model_manager.FixedNumTimePointsModelManager(buy_model_param)
    self.mm_buy_.init_for_serving()
    self.mm_sell_ = model_manager.FixedNumTimePointsModelManager(sell_model_param)
    self.mm_sell_.init_for_serving()

    # Please be cautious here, that sell model should have different name scope.
    # Otherwise it will overwrite what buy model has loaded.
    for var in tf.trainable_variables():
      if 'buy_' in var.name:
        buy_variables.append(var)
      elif 'sell_' in var.name:
        sell_variables.append(var)

    saver_buy = tf.train.Saver(var_list = buy_variables)
    saver_buy.restore(sess, buy_model_param.previous_model)

    saver_sell = tf.train.Saver(var_list = sell_variables)
    saver_sell.restore(sess, sell_model_param.previous_model)

    self.buy_score_dict_ = dict()
    self.sell_price_dict_ = dict()

    self.num_eligible_list_requirement_ = 100
    self.increase_check_threshold_ = 0.01
    self.decrease_check_threshold = -0.005

    self.buy_stock_prob_threshold_ = 0.65

    self.sell_within_day_ = False

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
    transaction.commission_fee = trade_strategy.k_commission_fee
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

    # First, sell all symbols that NN thinks it is time to sell
    for symbol in portfolio.get_current_hold_symbol_list():
      result, index = data_manager.get_symbol_minute_index(symbol, cur_time)
      if result == 2:
        continue

      one_symbol_data = data_manager.get_one_symbol_data(symbol)
      one_symbol_minute_data = one_symbol_data.data[index]

      if self.sell_within_day_:
        if cur_time > k_sell_all_time:
          result, transaction = self.__sell_one_symbol_completely(symbol, cur_time, one_symbol_minute_data.open, portfolio)
          if result:
            print transaction
            transactions.append(transaction)
            continue

      buy_price = portfolio.get_buy_price(symbol)
      increase_ratio = (one_symbol_minute_data.open - buy_price) / buy_price

      if not self.mm_sell_.is_eligible_to_be_fed_into_network(one_symbol_data, index):
        continue

      sell_score = self.mm_sell_.compute_prob(one_symbol_data, index)
      if sell_score > 0.5:
        if increase_ratio > self.increase_check_threshold_ or increase_ratio < self.decrease_check_threshold:
          result, transaction = self.__sell_one_symbol_completely(symbol, cur_time, one_symbol_minute_data.open,
                                                                  portfolio)
          if result:
            transactions.append(transaction)
            self.sell_price_dict_[symbol] = transaction.price

    if self.sell_within_day_ and cur_time > k_sell_all_time:
      return transactions

    if self.num_available_slot_ == 0:
      return transactions

    # Then let's see whether there is any stock that has highest score to buy
    for symbol in data_manager.get_available_symbol_list():
      if self.num_available_slot_ == 0:
        break

      result, index = data_manager.get_symbol_minute_index(symbol, cur_time)
      if result == 2:
        continue

      if portfolio.if_symbol_is_in_holding(symbol):
        continue

      one_symbol_data = data_manager.get_one_symbol_data(symbol)
      if not self.mm_buy_.is_eligible_to_be_fed_into_network(one_symbol_data, index):
        continue

      prob_score = self.mm_buy_.compute_prob(one_symbol_data, index)
      self.buy_score_dict_[symbol] = prob_score

    if len(self.buy_score_dict_) > self.num_eligible_list_requirement_:
      for symbol, score in sorted(self.buy_score_dict_.iteritems(), key=lambda (k,v): (v,k), reverse=True):
        if self.num_available_slot_ == 0:
          break

        if score < self.buy_stock_prob_threshold_:
          break

        if portfolio.if_symbol_is_in_holding(symbol):
          continue

        result, index = data_manager.get_symbol_minute_index(symbol, cur_time)
        if result == 2:
          continue

        one_symbol_data = data_manager.get_one_symbol_data(symbol)
        one_symbol_minute_data = one_symbol_data.data[index]

        if not self.mm_buy_.is_eligible_to_be_fed_into_network(one_symbol_data, index):
          continue

        if symbol in self.sell_price_dict_:
          if one_symbol_minute_data.open > self.sell_price_dict_[symbol] - self.increase_check_threshold_:
            continue

        buy_amount = int((portfolio.get_available_cash() - trade_strategy.k_commission_fee) /
                         self.num_available_slot_ / one_symbol_minute_data.open)
        transaction = stock_pb2.Transaction()
        transaction.type = stock_pb2.Transaction.BUY
        transaction.symbol = symbol
        transaction.amount = buy_amount
        transaction.commission_fee = trade_strategy.k_commission_fee
        transaction.price = one_symbol_minute_data.open
        transaction.date = self.date_int_val_
        transaction.time = cur_time

        if portfolio.buy_stock(transaction):
          transactions.append(transaction)
          self.num_available_slot_ -= 1

    return transactions