import simulation_pb2
import trade_strategy
import trade_strategy_buy_and_hold_one_stock

class BuyAndSellOneStockEODTradeStrategy(trade_strategy_buy_and_hold_one_stock.BuyAndHoldOneStockTradeStrategy):
  """ Trade strategy of buying one stock and sell it at EOD. """

  def run_minute_trade_strategy(self, data_manager, cur_time, portfolio):
    if not self.cur_day_load_result_:
      return []
    k_eod_time_threshold = 1255

    if cur_time < k_eod_time_threshold:
      return trade_strategy_buy_and_hold_one_stock.BuyAndHoldOneStockTradeStrategy.run_minute_trade_strategy(
        self, data_manager, cur_time, portfolio)

    # This means the stock is already sold
    if self.symbol_ not in portfolio.get_current_hold_symbol_list():
      return []

    result, one_time_data = data_manager.get_symbol_minute_data(self.symbol_, cur_time)
    if result == 1:
      return []

    transaction = simulation_pb2.Transaction()
    transaction.type = simulation_pb2.Transaction.SELL
    transaction.symbol = self.symbol_
    transaction.amount = portfolio.get_num_holding(self.symbol_)  # means sell all
    transaction.commission_fee = trade_strategy.k_commission_fee
    transaction.price = one_time_data.open
    transaction.date = self.date_int_val_
    transaction.time = cur_time

    transactions = []
    if portfolio.sell_stock(transaction):
      transactions.append(transaction)

    return transactions