import argparse
import sys
import tensorflow as tf

import sim_environment.simulation as simulation
import sim_environment.trade_strategy as trade_strategy
import sim_environment.trade_strategy_ai as trade_strategy_ai

import proto.trade_strategy_param_pb2 as trade_strategy_param_pb2
import proto.nn_train_param_pb2 as nn_train_param_pb2
import util.data_provider as data_provider
import util.sim_html_report as html_report

FLAGS=None

k_data_folder = './data/intra_day/'
def run_buy_drop_stock_trade_strategy():
  dp = data_provider.DataProvider(FLAGS.data_dir, FLAGS.use_eligible_list)
  
  start_date = 20180504
  end_date = 20180531
  initial_fund = 100000

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
  strategy = trade_strategy.BuyAndHoldOneStockTradeStrategy('AMZN')
  
  #strategy = trade_strategy.BuyDropStockTradeStrategy(params)
  
  sim.set_trade_strategy(strategy)
  sim.set_data_manager(dp)
  
  sim.run()
  transactions, datetime_list, balance = sim.get_simulation_run_result()
  report = html_report.SimulationHtmlReport(sim_name, transactions, datetime_list, balance, skip_details=False)
  report.export('./report')

def run_ai_trade_strategy():
  dp = data_provider.DataProvider(FLAGS.data_dir, FLAGS.use_eligible_list)

  start_date = 20180507
  end_date = 20180531
  initial_fund = 100000

  sim_name = 'BuyDropStockTradeStrategy'
  sim = simulation.Simulation(sim_name)
  sim.set_start_date(start_date)
  sim.set_end_date(end_date)
  sim.deposit_fund(initial_fund)


  trade_param = nn_train_param_pb2.TradeParamAI()
  trade_param.buy_param.use_cnn = True
  if trade_param.buy_param.use_cnn:
    trade_param.buy_param.architecture.extend([4, 8, 4, 8])
  else:
    trade_param.buy_param.architecture.extend([32, 32])
  trade_param.buy_param.previous_model = './model/buy_classifier/model_classification_12.ckpt'
  trade_param.buy_param.num_time_points = 100
  trade_param.buy_param.upper_time_point_limit = 149
  trade_param.buy_param.type = nn_train_param_pb2.TrainingParams.CLASSIFY_FUTURE_HIGHEST_PRICE
  trade_param.buy_param.use_relative_price_percentage_to_buy = False
  trade_param.buy_param.relative_price_percentage = 0.5
  trade_param.buy_param.use_pre_market_data = False
  trade_param.buy_param.dense_ratio = 0.8
  trade_param.buy_param.average_cash_flow_per_min = 20000.0
  trade_param.buy_param.use_relative_price_percentage_to_buy = True
  trade_param.buy_param.relative_price_percentage = 0.5

  trade_param.sell_param.use_cnn = True
  if trade_param.sell_param.use_cnn:
    trade_param.sell_param.architecture.extend([4, 8, 4, 8])
  else:
    trade_param.sell_param.architecture.extend([32, 32])
  trade_param.sell_param.previous_model = './model/sell_classifier/model_classification_13.ckpt'
  trade_param.sell_param.num_time_points = 100
  trade_param.sell_param.upper_time_point_limit = 10000
  trade_param.sell_param.type = nn_train_param_pb2.TrainingParams.CLASSIFY_BUY_SELL_TIME
  trade_param.sell_param.use_pre_market_data = False
  trade_param.sell_param.dense_ratio = 0.8
  trade_param.sell_param.average_cash_flow_per_min = 20000.0

  with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    strategy = trade_strategy_ai.BuyBestAIRankedTradeStrategy(sess, trade_param)

    sim.set_trade_strategy(strategy)
    sim.set_data_manager(dp)

    sim.run()
    transactions, datetime_list, balance = sim.get_simulation_run_result()
    report = html_report.SimulationHtmlReport(sim_name, transactions, datetime_list, balance, skip_details=False)
    report.export('./report')


def main(_):
  #run_buy_drop_stock_trade_strategy()
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
