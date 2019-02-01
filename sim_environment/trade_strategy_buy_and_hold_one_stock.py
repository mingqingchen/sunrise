import simulation_pb2
import trade_strategy

class BuyAndHoldOneStockTradeStrategy(trade_strategy.TradeStrategy):
  """ Trade strategy of buying one stock and hold forever. """

  def __init__(self, name):
    self.symbol_ = name

  def update_date(self, date_int_val, data_manager):
    """ This provides needed operations when a new day is updated.
        For buy and hold one stock strategy, we just need to deserialize one stock
    """
    self.date_int_val_ = date_int_val
    self.cur_day_load_result_ = data_manager.load_one_symbol_data(date_int_val, self.symbol_)
    return

  def run_minute_trade_strategy(self, data_manager, cur_time, portfolio):
    if not self.cur_day_load_result_:
      return []

    available_cash = portfolio.get_available_cash()
    transaction = simulation_pb2.Transaction()

    # Try to check whether cur_time is in the recording
    # It is possible that cur_time is not in the recording, since the data is not perfect
    # If it is not in the recording, just returns
    result, one_time_data = data_manager.get_symbol_minute_data(self.symbol_, cur_time)
    if result != 0:
      return []

    buy_amount = int((available_cash - trade_strategy.k_commission_fee) / one_time_data.open)
    if buy_amount <= 0:
      return []

    transaction.type = simulation_pb2.Transaction.BUY
    transaction.symbol = self.symbol_
    transaction.amount = buy_amount
    transaction.commission_fee = trade_strategy.k_commission_fee
    transaction.price = one_time_data.open
    transaction.date = self.date_int_val_
    transaction.time = cur_time

    print transaction

    transactions = []
    if portfolio.buy_stock(transaction):
      transactions.append(transaction)

    return transactions
