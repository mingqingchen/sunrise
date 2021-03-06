import sim_environment.simulation as simulation
import sim_environment.simulation_pb2 as simulation_pb2
import sim_environment.trade_strategy_buy_and_hold_one_stock as trade_strategy_buy_and_hold_one_stock
import sim_environment.trade_strategy_buy_and_sell_one_stock_eod as trade_strategy_buy_and_sell_one_stock_eod
import util.data_provider as data_provider
import util.sim_html_report as sim_html_report
import common_test_util
import unittest


class TestSimulation(unittest.TestCase):
  def test_basic_buy_and_hold_strategy(self):
    sim = simulation.Simulation('basic simulation')
    dp = data_provider.DataProvider('./data/minute_data/', use_eligible_list=False)
    strategy = trade_strategy_buy_and_hold_one_stock.BuyAndHoldOneStockTradeStrategy('AMZN')
    sim.set_start_date(20180417)
    sim.set_end_date(20190117)
    sim.set_data_manager(dp)
    sim.deposit_fund(100000)  # 100K
    sim.set_trade_strategy(strategy)

    sim.run()

    transactions, date_time_list, balances = sim.get_simulation_run_result()

    self.assertEqual(len(transactions), 1)
    self.assertEqual(transactions[0].symbol, 'AMZN')
    self.assertEqual(transactions[0].amount, int((100000 - 7) / transactions[0].price))
    self.assertEqual(transactions[0].date, 20180417)

    self.assertEqual(len(date_time_list), len(balances))

    report = sim_html_report.SimulationHtmlReport(
      'Basic buy and hold', transactions, date_time_list, balances, skip_details=False)
    report.export('./report_buy_and_hold_amzn', dp)

  def test_buy_and_sell_eod_strategy(self):
    sim = simulation.Simulation('basic simulation')
    dp = data_provider.DataProvider('./data/minute_data/', use_eligible_list=False)
    symbol = 'AMZN'
    strategy = trade_strategy_buy_and_sell_one_stock_eod.BuyAndSellOneStockEODTradeStrategy(symbol)

    initial_deposit = 100000  # 100K

    sim.set_start_date(20190101)
    sim.set_end_date(20190117)
    sim.set_data_manager(dp)
    sim.deposit_fund(initial_deposit)
    sim.set_trade_strategy(strategy)

    sim.run()

    transactions, datetime_list, balances = sim.get_simulation_run_result()

    self.assertEqual(len(datetime_list), len(balances))

    # each day should only have one sell action
    sell_date_set = set()
    for transaction in transactions:
      if transaction.type == simulation_pb2.Transaction.SELL:
        self.assertFalse(transaction.date in sell_date_set)
        sell_date_set.add(transaction.date)

    amount = common_test_util.check_transaction_correct(initial_deposit, transactions)
    self.assertGreaterEqual(amount, 0)
    self.assertAlmostEqual(amount, balances[-1], delta=0.1)

    report = sim_html_report.SimulationHtmlReport(
      'Basic buy and sell EOD', transactions, datetime_list, balances, skip_details=False)
    report.export('./report_buy_and_sell_amzn', dp)


if __name__ == "__main__":
  unittest.main()
