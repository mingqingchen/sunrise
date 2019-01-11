import argparse
import datetime_util
import matplotlib.pyplot as plt
import os, sys
import shutil
import tensorflow as tf

import data_provider


def main():
  dp_minute = data_provider.DataProvider('./data/intra_day', use_eligible_list=False)
  dp_daily = data_provider.DataProvider('./data/daily_data', use_eligible_list=False)

  all_dates = dp_minute.get_all_available_dates()

  last_day = 20181201

  symbol_list = dp_daily.get_symbol_list_for_a_day(2018)
  symbol_list_set = set()
  for symbol in symbol_list:
    symbol_list_set.add(symbol)

  for date_val in all_dates:
    date_val = int(date_val)
    if date_val > last_day:
      break
    dp_minute.load_one_day_data(date_val)
    all_symbols = dp_minute.get_symbol_list_for_a_day(date_val)

    for symbol in all_symbols:
      if symbol not in symbol_list_set:
        print('Symbol %s does not exist in daily data.' % symbol)
        continue
      if not dp_minute.load_one_symbol_data(date_val, symbol):
        print('Could not load %s on day %d' % (symbol, date_val))
      one_day_minute_data = dp_minute.get_one_symbol_data(symbol)
      if not dp_daily.load_one_symbol_data(2018, symbol):
        print('Could not find daily data for %s' % symbol)
      for try_match_date in [date_val, date_val - 1]:
        result, one_day_summary_data = dp_daily.get_symbol_minute_data(symbol, try_match_date)
        if result == 0 or result == 1:
          if data_provider.is_one_day_a_match(one_day_minute_data, one_day_summary_data):
            matched_date = one_day_summary_data.time_val
            day_folder = 'data/minute_data/%d' % matched_date
            if not os.path.isdir(day_folder):
              os.makedirs(day_folder)
            print('A good match on %d: %s' % (try_match_date, symbol))
            shutil.move('./data/intra_day/%d/%s.pb' % (date_val, symbol), './data/minute_data/%d/%s.pb' % (matched_date, symbol))
            break





if __name__=="__main__":
  main()