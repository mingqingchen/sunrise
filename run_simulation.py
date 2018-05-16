import argparse
import sys
import tensorflow as tf

import sim_environment.simulation as simulation
import sim_environment.trade_strategy as trade_strategy
import sim_environment.trade_strategy_ai as trade_strategy_ai
import util.display_util as display_util

import proto.trade_strategy_param_pb2 as trade_strategy_param_pb2
import proto.nn_train_param_pb2 as nn_train_param_pb2
import util.data_provider as data_provider
import util.sim_html_report as html_report

FLAGS=None

k_data_folder = './data/intra_day/'
def run_buy_drop_stock_trade_strategy():
  dp = data_provider.DataProvider(FLAGS.data_dir, FLAGS.use_eligible_list)
  
  start_date = 20180417
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

def run_ai_trade_strategy():
  dp = data_provider.DataProvider(FLAGS.data_dir, FLAGS.use_eligible_list)

  start_date = 20180501
  end_date = 20180515
  initial_fund = 100000

  du = display_util.DisplayUtil()

  sim_name = 'BuyDropStockTradeStrategy'
  sim = simulation.Simulation(sim_name)
  sim.set_start_date(start_date)
  sim.set_end_date(end_date)
  sim.deposit_fund(initial_fund)

  param_buy = nn_train_param_pb2.TrainingParams()
  param_buy.architecture.extend([32, 32])
  param_buy.previous_model = './model/threshold_0.005/model_classification_25.ckpt'
  param_buy.num_time_points = 100
  param_buy.upper_time_point_limit = 149
  param_buy.type = nn_train_param_pb2.TrainingParams.CLASSIFY_FUTURE_HIGHEST_PRICE
  param_buy.use_relative_price_percentage_to_buy = False
  param_buy.relative_price_percentage = 0.5
  param_buy.use_pre_market_data = False

  param_sell = nn_train_param_pb2.TrainingParams()
  param_sell.architecture.extend([32, 32])
  param_sell.previous_model = './model/sell_classifier/model_classification_25.ckpt'
  param_sell.num_time_points = 100
  param_sell.upper_time_point_limit = 10000
  param_sell.type = nn_train_param_pb2.TrainingParams.CLASSIFY_BUY_SELL_TIME
  param_sell.use_pre_market_data = False

  with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    strategy = trade_strategy_ai.BuyBestAIRankedTradeStrategy(sess, param_buy, param_sell)

    sim.set_trade_strategy(strategy)
    sim.set_data_manager(dp)

    sim.run()
    transactions, datetime_list, balance = sim.get_simulation_run_result()
    report = html_report.SimulationHtmlReport(sim_name, transactions, datetime_list, balance)
    report.export('./report')


def main(_):
  run_ai_trade_strategy()
  
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
