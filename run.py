import argparse
import os
import sys
import tensorflow as tf


import sim_environment.simulation as simulation
import sim_environment.trade_strategy as trade_strategy
import util.display_util as display_util

import proto.stock_pb2 as stock_pb2
import util.datetime_util as datetime_util
import util.data_provider as data_provider
import util.sim_html_report as html_report


FLAGS=None

k_data_folder = './data/intra_day/'
def main(_):
  dp = data_provider.DataProvider(FLAGS.data_dir)
  
  start_date = 20180416
  end_date = 20180423
  initial_fund = 200000

  du = display_util.DisplayUtil()
  
  if False:
    stock_list = ['AMZN', 'ISRG']
    for stock_name in stock_list:
      sim_name = 'Buy {0} and hold'.format(stock_name)
      sim = simulation.Simulation(sim_name)
      sim.set_start_date(start_date)
      sim.set_end_date(end_date)
      sim.deposit_fund(initial_fund)
      strategy = trade_strategy.BuyAndHoldOneStockTradeStrategy(stock_name)
      sim.set_trade_strategy(strategy)
      sim.set_data_manager(dp)
  
      sim.run()
      transactions, datetime_list, balance = sim.get_simulation_run_result()
      du.add_one_simulation_result(sim_name, transactions, datetime_list, balance)
  
    for stock_name in stock_list:
      sim_name = 'Buy {0} and sell EOD'.format(stock_name)
      sim = simulation.Simulation(sim_name)
      sim.set_start_date(start_date)
      sim.set_end_date(end_date)
      sim.deposit_fund(initial_fund)
      strategy = trade_strategy.BuyAndSellOneStockEODTradeStrategy(stock_name)
      sim.set_trade_strategy(strategy)
      sim.set_data_manager(dp)
  
      sim.run()
      transactions, datetime_list, balance = sim.get_simulation_run_result()
      du.add_one_simulation_result(sim_name, transactions, datetime_list, balance)

  sim_name = 'BuyDropStockTradeStrategy'
  sim = simulation.Simulation(sim_name)
  sim.set_start_date(start_date)
  sim.set_end_date(end_date)
  sim.deposit_fund(initial_fund)
  strategy = trade_strategy.BuyDropStockTradeStrategy(watch_time = 30, drop_threshold=-0.02, watch_time_drop_threshold=-0.015, rebound_sell_threshold=0.01, num_slot=10)
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
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
