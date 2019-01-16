import os
import shutil

import data_provider


def main():
  dp_minute = data_provider.DataProvider('./data/minute_data_unverified', use_eligible_list=False)
  dp_daily = data_provider.DataProvider('./data/daily_data', use_eligible_list=False)

  all_dates = dp_minute.get_all_available_dates()

  if False:
    for year in [2019]:
      symbol_list = dp_daily.get_symbol_list_for_a_day(year)
      dp_daily.load_one_day_data(year)
      for symbol in symbol_list:
        print('symbol: %s, year: %d' % (symbol, year))
        one_symbol = dp_daily.get_one_symbol_data(symbol)
        one_symbol = data_provider.sort_data_based_on_time(one_symbol)
        output_file_path = os.path.join("./data/daily_data/%d/" % year, symbol + '.pb')
        fid = open(output_file_path, 'w')
        fid.write(one_symbol.SerializeToString())
        fid.close()

  symbol_list = dp_daily.get_symbol_list_for_a_day(2019)
  symbol_list_set = set()
  for symbol in symbol_list:
    symbol_list_set.add(symbol)

  for date_val in all_dates:
    date_val = int(date_val)
    if date_val < 20190101:
      continue
    dp_minute.load_one_day_data(date_val)
    all_symbols = dp_minute.get_symbol_list_for_a_day(date_val)

    for symbol in all_symbols:
      if symbol not in symbol_list_set:
        print('Symbol %s does not exist in daily data.' % symbol)
        continue
      if not dp_minute.load_one_symbol_data(date_val, symbol):
        continue
      if not dp_daily.load_one_symbol_data(2019, symbol):
        continue
      one_day_minute_data = dp_minute.get_one_symbol_data(symbol)
      for try_match_date in [date_val, date_val - 1]:
        result, one_day_summary_data = dp_daily.get_symbol_minute_data(symbol, try_match_date)
        if result == 0 or result == 1:
          if data_provider.is_one_day_a_match(one_day_minute_data, one_day_summary_data, False):
            matched_date = one_day_summary_data.time_val
            day_folder = 'data/minute_data/%d' % matched_date
            if not os.path.isdir(day_folder):
              os.makedirs(day_folder)
            print('A good match on %d: %s' % (try_match_date, symbol))
            src_file_path = './data/minute_data_unverified/%d/%s.pb' % (date_val, symbol)
            dst_file_path = './data/minute_data/%d/%s.pb' % (matched_date, symbol)
            if not os.path.isfile(dst_file_path):
              shutil.copyfile(src_file_path, dst_file_path)
            break






if __name__=="__main__":
  main()
