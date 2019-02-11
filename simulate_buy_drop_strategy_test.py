import sim_environment.simulation as simulation
import sim_environment.trade_strategy_buy_drop_stock as trade_strategy_buy_drop_stock
import util.data_provider as data_provider
import util.sim_html_report as sim_html_report
import sim_environment.trade_strategy_pb2 as trade_strategy_pb2
import common_test_util
import unittest


class TestSimulation(unittest.TestCase):

  def test_buy_drop_strategy(self):
    sim = simulation.Simulation('basic simulation')
    dp = data_provider.DataProvider('./data/minute_data/', use_eligible_list=False)

    params = trade_strategy_pb2.BuyDropStrategyParam()
    params.num_slot = 5
    params.minimal_timepoint = 20
    params.minimal_price = 2.0
    params.drop_threshold = -0.02
    params.num_buy_time = 1
    params.rebound_sell_threshold = 0.02
    params.stop_loss_sell_threshold = -0.02
    strategy = trade_strategy_buy_drop_stock.BuyDropStockTradeStrategy(params)

    initial_deposit = 100000  # 100K

    sim.set_start_date(20190101)
    sim.set_end_date(20190228)
    sim.set_data_manager(dp)
    sim.deposit_fund(initial_deposit)
    sim.set_trade_strategy(strategy)

    sim.run()

    transactions, datetime_list, balances = sim.get_simulation_run_result()

    self.assertEqual(len(datetime_list), len(balances))

    amount = common_test_util.check_transaction_correct(initial_deposit, transactions)
    self.assertGreaterEqual(amount, 0)

    report = sim_html_report.SimulationHtmlReport(
      'Buy drop strategy', transactions, datetime_list, balances, skip_details=False)
    report.export('./report_buy_drop', dp)


if __name__ == "__main__":
  unittest.main()
