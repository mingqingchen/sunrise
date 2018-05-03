import argparse
import os
import sys
import tensorflow as tf


import sim_environment.simulation as simulation
import sim_environment.trade_strategy as trade_strategy
import util.display_util as display_util

import proto.stock_pb2 as stock_pb2
import proto.trade_strategy_param_pb2 as trade_strategy_param_pb2
import util.datetime_util as datetime_util
import util.data_provider as data_provider
import util.sim_html_report as html_report


FLAGS=None

k_data_folder = './data/intra_day/'
def main(_):
  dp = data_provider.DataProvider(FLAGS.data_dir, FLAGS.use_eligible_list)
  
  start_date = 20180501
  end_date = 20180502
  initial_fund = 200000

  du = display_util.DisplayUtil()
  
  sim_name = 'BuyDropStockTradeStrategy'
  sim = simulation.Simulation(sim_name)
  sim.set_start_date(start_date)
  sim.set_end_date(end_date)
  sim.deposit_fund(initial_fund)
  params = trade_strategy_param_pb2.BuyDropTradeStrategyParam()
  params.watch_time = 30
  params.drop_threshold = -0.02
  params.watch_time_drop_threshold = -0.015
  params.rebound_sell_threshold = 0.02
  params.stop_loss_sell_threshold = - 0.02
  params.num_slot = 10
  params.num_buy_time = 1
  params.minimal_price = 5.0
  params.minimal_timepoint = 50
  
  # Here you can replace with other trade strategies, e.g.
  # strategy = trade_strategy.BuyAndHoldOneStockTradeStrategy('AMZN')
  # strategy = trade_strategy.BuyAndSellOneStockEODTradeStrategy('AMZN')
  
  strategy = trade_strategy.BuyDropStockTradeStrategy(params)
  
  sim.set_trade_strategy(strategy)
  sim.set_data_manager(dp)
  
  sim.run()
  transactions, datetime_list, balance = sim.get_simulation_run_result()
  report = html_report.SimulationHtmlReport(sim_name, transactions, datetime_list, balance)
  report.export('./report')
  #du.add_one_simulation_result(sim_name, transactions, datetime_list, balance)
  #du.display()

  
if __name__=="__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--data_dir',
    type=str,
    default=k_data_folder,
    help='Root for historical data'
  )

  parser.add_argument(
    '--use_eligible_list',
    type=bool,
    default=True,
    help='Whether use eligible list or not'
  )
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
