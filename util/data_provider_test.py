import data_provider
import os
import stock_pb2
import unittest

k_tmp_folder = '/tmp/sunrise_unit_test/'


def create_folder_if_not_exist(folder):
  if not os.path.isdir(folder):
    os.mkdir(folder)


def remove_folder_if_exist(folder):
  if os.path.isdir(folder):
    os.removedirs(folder)

def add_one_stock_data(symbol, date, resolution):
  one_stock_data = stock_pb2.OneIntraDayData()
  one_stock_data.symbol = symbol
  one_stock_data.date = date
  one_stock_data.resolution = resolution
  return one_stock_data

def add_one_time_slot_data(one_intra_day_data, time_val, open, close, high, low, volume):
  one_time_data = one_intra_day_data.data.add()
  one_time_data.time_val = time_val
  one_time_data.open = open
  one_time_data.close = close
  one_time_data.high = high
  one_time_data.low = low
  one_time_data.volume = volume

def write_one_stock_data(one_stock_data):
  file_path = os.path.join(k_tmp_folder, str(one_stock_data.date), one_stock_data.symbol + '.pb')
  fid = open(file_path, 'w')
  fid.write(one_stock_data.SerializeToString())
  fid.close()

def build_data_set():
  create_folder_if_not_exist(k_tmp_folder)
  create_folder_if_not_exist(os.path.join(k_tmp_folder, '20181228'))
  create_folder_if_not_exist(os.path.join(k_tmp_folder, '20181230'))
  create_folder_if_not_exist(os.path.join(k_tmp_folder, '20181231'))
  create_folder_if_not_exist(os.path.join(k_tmp_folder, '20190101'))
  create_folder_if_not_exist(os.path.join(k_tmp_folder, '20190104'))

  one_stock_data = add_one_stock_data('GOOGL', 20181230, 1)
  # be careful, number starts with 0, e.g. 0601 is not decimal
  add_one_time_slot_data(one_stock_data, 601, 990.0, 991.0, 991.5, 989.5, 2000)
  add_one_time_slot_data(one_stock_data, 602, 991.0, 992.0, 992.1, 990.9, 1000)
  add_one_time_slot_data(one_stock_data, 605, 992.0, 1000.0, 1000.6, 991.8, 5000)
  write_one_stock_data(one_stock_data)

  one_stock_data = add_one_stock_data('AMZN', 20181228, 1)
  add_one_time_slot_data(one_stock_data, 401, 1400.0, 1410.0, 1415.0, 1400.0, 3000)
  write_one_stock_data(one_stock_data)

  one_stock_data = add_one_stock_data('AMZN', 20181230, 1)
  add_one_time_slot_data(one_stock_data, 601, 1400.0, 1410.0, 1415.0, 1400.0, 3000)
  add_one_time_slot_data(one_stock_data, 603, 1410.0, 1390.0, 1415.0, 1390.0, 2000)
  add_one_time_slot_data(one_stock_data, 605, 1390.0, 1380.0, 1393.0, 1370.0, 1000)
  add_one_time_slot_data(one_stock_data, 610, 1380.0, 1360.0, 1380.0, 1360.0, 2000)
  write_one_stock_data(one_stock_data)

  one_stock_data = add_one_stock_data('AMZN', 20190104, 1)
  add_one_time_slot_data(one_stock_data, 601, 1400.0, 1410.0, 1415.0, 1400.0, 3000)
  add_one_time_slot_data(one_stock_data, 602, 1410.0, 1390.0, 1415.0, 1390.0, 2000)
  add_one_time_slot_data(one_stock_data, 610, 1390.0, 1380.0, 1393.0, 1370.0, 1000)
  add_one_time_slot_data(one_stock_data, 630, 1380.0, 1360.0, 1380.0, 1360.0, 2000)
  write_one_stock_data(one_stock_data)


class TestDataProvider(unittest.TestCase):
  def test_sort_data(self):
    one_stock_data = add_one_stock_data('GOOGL', 20181230, 1)
    # be careful, number starts with 0, e.g. 0601 is not decimal
    add_one_time_slot_data(one_stock_data, 2359, 990.0, 991.0, 991.5, 989.5, 2000)
    add_one_time_slot_data(one_stock_data, 602, 991.0, 992.0, 992.1, 990.9, 1000)
    add_one_time_slot_data(one_stock_data, 603, 992.0, 1000.0, 1000.6, 991.8, 5000)
    add_one_time_slot_data(one_stock_data, 601, 992.0, 1000.0, 1000.6, 991.8, 5000)

    sorted_data = data_provider.sort_data_based_on_time(one_stock_data)
    self.assertEqual(sorted_data.symbol, 'GOOGL')
    self.assertEqual(sorted_data.date, 20181230)
    self.assertEqual(sorted_data.resolution, 1)
    self.assertEqual(len(sorted_data.data), 4)

    self.assertEqual(sorted_data.data[0].time_val, 601)
    self.assertEqual(sorted_data.data[1].time_val, 602)
    self.assertEqual(sorted_data.data[2].time_val, 603)
    self.assertEqual(sorted_data.data[3].time_val, 2359)


  def test_is_match(self):
    dp_minute = data_provider.DataProvider('./data/minute_data', use_eligible_list=False)
    dp_daily = data_provider.DataProvider('./data/daily_data', use_eligible_list=False)

    start_date = 20180719
    end_date = 20191231

    year_loaded_map = {2018: False, 2019: False}

    for date_val in dp_minute.get_all_available_dates():
      date_val = int(date_val)
      if date_val < start_date or date_val > end_date:
        continue

      year = date_val / 10000
      if not year_loaded_map[year]:
        dp_daily.load_one_day_data(year)
        year_loaded_map[year] = True

      dp_minute.load_one_day_data(date_val)
      for symbol in dp_minute.get_available_symbol_list():
        self.assertTrue(symbol in dp_daily.get_available_symbol_list())
        self.assertTrue(dp_minute.load_one_symbol_data(date_val, symbol))
        one_day_minute_data = dp_minute.get_one_symbol_data(symbol)
        if len(one_day_minute_data.data) < 20:
          continue
        print('Checking symbol %s on %d' % (symbol, date_val))
        result, one_day_summary_data = dp_daily.get_symbol_minute_data(symbol, date_val)
        self.assertEqual(result, 0)
        result_without_include = data_provider.is_one_day_a_match(one_day_minute_data, one_day_summary_data, False)
        result_include = data_provider.is_one_day_a_match(one_day_minute_data, one_day_summary_data, True)
        self.assertTrue(result_without_include or result_include)
        print('Good match for %s on day %d' % (symbol, date_val))


  def test_merge_data_1(self):
    one_stock_data_a = stock_pb2.OneIntraDayData()
    one_stock_data_a.symbol = 'AMZN'
    one_stock_data_b = stock_pb2.OneIntraDayData()
    one_stock_data_b.symbol = 'MSFT'
    result, _ = data_provider.merge_one_intra_day_data(one_stock_data_a, one_stock_data_b)
    self.assertFalse(result)

  def test_merge_data_2(self):
    one_stock_data_a = stock_pb2.OneIntraDayData()
    one_stock_data_a.symbol = 'AMZN'
    one_stock_data_a.date = 20180305
    one_stock_data_b = stock_pb2.OneIntraDayData()
    one_stock_data_b.symbol = 'AMZN'
    one_stock_data_b.date = 20180306
    result, _ = data_provider.merge_one_intra_day_data(one_stock_data_a, one_stock_data_b)
    self.assertFalse(result)

  def test_merge_data_3(self):
    one_stock_data_a = stock_pb2.OneIntraDayData()
    one_stock_data_a.symbol = 'AMZN'
    one_stock_data_a.date = 20180305
    one_stock_data_a.resolution = 1
    one_stock_data_b = stock_pb2.OneIntraDayData()
    one_stock_data_b.symbol = 'AMZN'
    one_stock_data_b.date = 20180305
    one_stock_data_b.resolution = 3
    result, _ = data_provider.merge_one_intra_day_data(one_stock_data_a, one_stock_data_b)
    self.assertFalse(result)

  def test_merge_data_4(self):
    one_stock_data_a = stock_pb2.OneIntraDayData()
    one_stock_data_a.symbol = 'AMZN'
    one_stock_data_a.date = 20180305
    one_stock_data_a.resolution = 1
    add_one_time_slot_data(one_stock_data_a, 630, 1.0, 1.0, 1.0, 1.0, 2000)
    add_one_time_slot_data(one_stock_data_a, 631, 1.0, 1.0, 1.0, 1.0, 2000)
    add_one_time_slot_data(one_stock_data_a, 638, 1.0, 1.0, 1.0, 1.0, 2000)
    add_one_time_slot_data(one_stock_data_a, 650, 1.0, 1.0, 1.0, 1.0, 2000)

    one_stock_data_b = stock_pb2.OneIntraDayData()
    one_stock_data_b.symbol = 'AMZN'
    one_stock_data_b.date = 20180305
    one_stock_data_b.resolution = 1
    add_one_time_slot_data(one_stock_data_b, 631, 1.0, 1.0, 1.0, 1.0, 2000)
    add_one_time_slot_data(one_stock_data_b, 637, 1.0, 1.0, 1.0, 1.0, 2000)
    add_one_time_slot_data(one_stock_data_b, 638, 1.0, 1.0, 1.0, 1.0, 2000)

    result, merged_data = data_provider.merge_one_intra_day_data(one_stock_data_a, one_stock_data_b)
    self.assertTrue(result)
    self.assertEqual(len(merged_data.data), 5)
    self.assertEqual(merged_data.data[0].time_val, 630)
    self.assertEqual(merged_data.data[1].time_val, 631)
    self.assertEqual(merged_data.data[2].time_val, 637)
    self.assertEqual(merged_data.data[3].time_val, 638)
    self.assertEqual(merged_data.data[4].time_val, 650)

  def test_merge_data_5(self):
    one_stock_data_a = stock_pb2.OneIntraDayData()
    one_stock_data_a.symbol = 'AMZN'
    one_stock_data_a.date = 20180305
    one_stock_data_a.resolution = 1
    add_one_time_slot_data(one_stock_data_a, 630, 1.0, 1.0, 1.0, 1.0, 2000)
    add_one_time_slot_data(one_stock_data_a, 631, 1.0, 1.0, 1.0, 1.0, 2000)
    add_one_time_slot_data(one_stock_data_a, 638, 1.0, 1.0, 1.0, 1.0, 2000)
    add_one_time_slot_data(one_stock_data_a, 650, 1.0, 1.0, 1.0, 1.0, 2000)

    one_stock_data_b = stock_pb2.OneIntraDayData()
    one_stock_data_b.symbol = 'AMZN'
    one_stock_data_b.date = 20180305
    one_stock_data_b.resolution = 1

    result, merged_data = data_provider.merge_one_intra_day_data(one_stock_data_a, one_stock_data_b)
    self.assertTrue(result)
    self.assertEqual(len(merged_data.data), 4)
    self.assertEqual(merged_data.data[0].time_val, 630)
    self.assertEqual(merged_data.data[1].time_val, 631)
    self.assertEqual(merged_data.data[2].time_val, 638)
    self.assertEqual(merged_data.data[3].time_val, 650)

  def test_get_all_dates(self):
    build_data_set()
    dp = data_provider.DataProvider(k_tmp_folder, use_eligible_list=False)
    all_dates_list = dp.get_all_available_dates()
    self.assertListEqual(all_dates_list, ['20181228', '20181230', '20181231', '20190101', '20190104'])

  def test_next_record_day(self):
    build_data_set()
    dp = data_provider.DataProvider(k_tmp_folder, use_eligible_list=False)
    self.assertEqual(dp.next_record_day(20170504), 20181228)
    self.assertEqual(dp.next_record_day(20181230), 20181231)
    self.assertEqual(dp.next_record_day(20181231), 20190101)
    self.assertEqual(dp.next_record_day(20190101), 20190104)
    self.assertEqual(dp.next_record_day(20190104), -1)
    self.assertEqual(dp.next_record_day(20190108), -1)

  def test_load_one_symbol_data(self):
    build_data_set()
    dp = data_provider.DataProvider(k_tmp_folder, use_eligible_list=False)
    self.assertTrue(dp.load_one_symbol_data(20181230, 'GOOGL'))
    self.assertTrue(dp.load_one_symbol_data(20181230, 'AMZN'))
    self.assertFalse(dp.load_one_symbol_data(20181231, 'GOOGL'))

    one_stock_data = dp.get_one_symbol_data('GOOGL')
    self.assertEqual(one_stock_data.symbol, 'GOOGL')
    self.assertEqual(one_stock_data.date, 20181230)
    self.assertEqual(len(one_stock_data.data), 3)

    one_stock_data = dp.get_one_symbol_data('AMZN')
    self.assertEqual(one_stock_data.symbol, 'AMZN')
    self.assertEqual(one_stock_data.date, 20181230)
    self.assertEqual(len(one_stock_data.data), 4)

    self.assertListEqual(dp.get_available_symbol_list(), ['AMZN', 'GOOGL'])

    self.assertTrue(dp.load_one_symbol_data(20190104, 'AMZN'))
    self.assertListEqual(dp.get_available_symbol_list(), ['AMZN', 'GOOGL'])

  def test_load_one_day_data(self):
    build_data_set()
    dp = data_provider.DataProvider(k_tmp_folder, use_eligible_list=False)
    dp.load_one_day_data(20181230)

    one_stock_data = dp.get_one_symbol_data('GOOGL')
    self.assertEqual(one_stock_data.symbol, 'GOOGL')
    self.assertEqual(one_stock_data.date, 20181230)
    self.assertEqual(len(one_stock_data.data), 3)

    one_stock_data = dp.get_one_symbol_data('AMZN')
    self.assertEqual(one_stock_data.symbol, 'AMZN')
    self.assertEqual(one_stock_data.date, 20181230)
    self.assertEqual(len(one_stock_data.data), 4)

    self.assertListEqual(dp.get_available_symbol_list(), ['AMZN', 'GOOGL'])

    dp.load_one_day_data(20190104)
    self.assertListEqual(dp.get_available_symbol_list(), ['AMZN'])

    dp.load_one_day_data(20190103)
    self.assertListEqual(dp.get_available_symbol_list(), [])

  def test_minute_index(self):
    build_data_set()
    dp = data_provider.DataProvider(k_tmp_folder, use_eligible_list=False)
    dp.load_one_day_data(20181230)
    for i in range(3):  # test this for 3 rounds for the robustness of using cached minute index
      result, index = dp.get_symbol_minute_index('GOOGL', 601)
      self.assertEqual(result, 0)
      self.assertEqual(index, 0)
      result, index = dp.get_symbol_minute_index('GOOGL', 602)
      self.assertEqual(result, 0)
      self.assertEqual(index, 1)
      result, index = dp.get_symbol_minute_index('AMZN', 603)
      self.assertEqual(result, 0)
      self.assertEqual(index, 1)
      result, index = dp.get_symbol_minute_index('GOOGL', 603)
      self.assertEqual(result, 1)
      self.assertEqual(index, 1)
      result, index = dp.get_symbol_minute_index('GOOGL', 604)
      self.assertEqual(result, 1)
      self.assertEqual(index, 1)
      result, index = dp.get_symbol_minute_index('GOOGL', 605)
      self.assertEqual(result, 0)
      self.assertEqual(index, 2)
      result, index = dp.get_symbol_minute_index('AMZN', 606)
      self.assertEqual(result, 1)
      self.assertEqual(index, 2)
      result, index = dp.get_symbol_minute_index('GOOGL', 606)
      self.assertEqual(result, 2)
      self.assertEqual(index, 2)
      result, index = dp.get_symbol_minute_index('GOOGL', 710)
      self.assertEqual(result, 2)
      self.assertEqual(index, 2)
      result, index = dp.get_symbol_minute_index('AMZN', 620)
      self.assertEqual(result, 2)
      self.assertEqual(index, 3)
      dp.clear_symbol_index()  # need to clear symbol index, since it will go back from the beginning

  def test_minute_data(self):
    build_data_set()
    dp = data_provider.DataProvider(k_tmp_folder, use_eligible_list=False)
    dp.load_one_day_data(20181230)
    for i in range(3):  # test this for 3 rounds for the robustness of using cached minute index
      result, one_minute_data = dp.get_symbol_minute_data('GOOGL', 601)
      self.assertEqual(result, 0)
      self.assertEqual(one_minute_data.open, 990.0)
      result, one_minute_data = dp.get_symbol_minute_data('GOOGL', 602)
      self.assertEqual(result, 0)
      self.assertEqual(one_minute_data.open, 991.0)
      result, one_minute_data = dp.get_symbol_minute_data('AMZN', 603)
      self.assertEqual(result, 0)
      self.assertEqual(one_minute_data.open, 1410.0)
      result, one_minute_data = dp.get_symbol_minute_data('GOOGL', 603)
      self.assertEqual(result, 1)
      self.assertEqual(one_minute_data.open, 991.0)
      result, one_minute_data = dp.get_symbol_minute_data('GOOGL', 604)
      self.assertEqual(result, 1)
      self.assertEqual(one_minute_data.open, 991.0)
      result, one_minute_data = dp.get_symbol_minute_data('AMZN', 606)
      self.assertEqual(result, 1)
      self.assertEqual(one_minute_data.open, 1390.0)
      result, one_minute_data = dp.get_symbol_minute_data('GOOGL', 605)
      self.assertEqual(result, 0)
      self.assertEqual(one_minute_data.open, 992.0)
      result, one_minute_data = dp.get_symbol_minute_data('GOOGL', 607)
      self.assertEqual(result, 2)
      self.assertEqual(one_minute_data.open, 992.0)
      result, one_minute_data = dp.get_symbol_minute_data('AMZN', 629)
      self.assertEqual(result, 2)
      self.assertEqual(one_minute_data.open, 1380.0)

      dp.clear_symbol_index()  # need to clear symbol index, since it will go back from the beginning

  def test_extract_previous_n_timepoints(self):
    build_data_set()
    dp = data_provider.DataProvider(k_tmp_folder, use_eligible_list=False)

    result, prev_n_list = dp.extract_previous_n_timepoints('AMZN', 20190104, 630, 6)
    self.assertTrue(result)
    self.assertEqual(len(prev_n_list), 6)
    self.assertEqual(prev_n_list[0].time_val, 605)
    self.assertEqual(prev_n_list[1].time_val, 610)
    self.assertEqual(prev_n_list[2].time_val, 601)
    self.assertEqual(prev_n_list[3].time_val, 602)
    self.assertEqual(prev_n_list[4].time_val, 610)
    self.assertEqual(prev_n_list[5].time_val, 630)

    result, prev_n_list = dp.extract_previous_n_timepoints('AMZN', 20190104, 630, 8)
    self.assertTrue(result)
    self.assertEqual(len(prev_n_list), 8)
    self.assertEqual(prev_n_list[0].time_val, 601)
    self.assertEqual(prev_n_list[1].time_val, 603)
    self.assertEqual(prev_n_list[2].time_val, 605)
    self.assertEqual(prev_n_list[3].time_val, 610)
    self.assertEqual(prev_n_list[4].time_val, 601)
    self.assertEqual(prev_n_list[5].time_val, 602)
    self.assertEqual(prev_n_list[6].time_val, 610)
    self.assertEqual(prev_n_list[7].time_val, 630)

    result, prev_n_list = dp.extract_previous_n_timepoints('AMZN', 20190104, 630, 9)
    self.assertTrue(result)
    self.assertEqual(len(prev_n_list), 9)
    self.assertEqual(prev_n_list[0].time_val, 401)
    self.assertEqual(prev_n_list[1].time_val, 601)
    self.assertEqual(prev_n_list[2].time_val, 603)
    self.assertEqual(prev_n_list[3].time_val, 605)
    self.assertEqual(prev_n_list[4].time_val, 610)
    self.assertEqual(prev_n_list[5].time_val, 601)
    self.assertEqual(prev_n_list[6].time_val, 602)
    self.assertEqual(prev_n_list[7].time_val, 610)
    self.assertEqual(prev_n_list[8].time_val, 630)

    result, _ = dp.extract_previous_n_timepoints('AMZN', 20190104, 630, 10)
    self.assertFalse(result)

    result, prev_n_list = dp.extract_previous_n_timepoints('AMZN', 20190104, 630, 3)
    self.assertTrue(result)
    self.assertEqual(len(prev_n_list), 3)
    self.assertEqual(prev_n_list[0].time_val, 602)
    self.assertEqual(prev_n_list[1].time_val, 610)
    self.assertEqual(prev_n_list[2].time_val, 630)

    result, prev_n_list = dp.extract_previous_n_timepoints('AMZN', 20190104, 615, 3)
    self.assertTrue(result)
    self.assertEqual(len(prev_n_list), 3)
    self.assertEqual(prev_n_list[0].time_val, 601)
    self.assertEqual(prev_n_list[1].time_val, 602)
    self.assertEqual(prev_n_list[2].time_val, 610)

    result, prev_n_list = dp.extract_previous_n_timepoints('AMZN', 20190104, 631, 3)
    self.assertFalse(result)

  def test_extract_previous_timepoints(self):
    build_data_set()
    dp = data_provider.DataProvider(k_tmp_folder, use_eligible_list=False)

    prev_list = dp.extract_previous_timepoints('AMZN', 20190104, 630, 0, 19)
    self.assertEqual(len(prev_list), 1)
    self.assertEqual(prev_list[0].time_val, 630)

    prev_list = dp.extract_previous_timepoints('AMZN', 20190104, 630, 0, 20)
    self.assertEqual(len(prev_list), 2)
    self.assertEqual(prev_list[0].time_val, 610)
    self.assertEqual(prev_list[1].time_val, 630)

    prev_list = dp.extract_previous_timepoints('AMZN', 20190104, 630, 5, 19)
    self.assertEqual(len(prev_list), 4)
    self.assertEqual(prev_list[0].time_val, 601)
    self.assertEqual(prev_list[1].time_val, 602)
    self.assertEqual(prev_list[2].time_val, 610)
    self.assertEqual(prev_list[3].time_val, 630)

    prev_list = dp.extract_previous_timepoints('AMZN', 20190104, 630, 5, 20)
    self.assertEqual(len(prev_list), 5)
    self.assertEqual(prev_list[0].time_val, 610)
    self.assertEqual(prev_list[1].time_val, 601)
    self.assertEqual(prev_list[2].time_val, 602)
    self.assertEqual(prev_list[3].time_val, 610)
    self.assertEqual(prev_list[4].time_val, 630)

    prev_list = dp.extract_previous_timepoints('AMZN', 20190104, 630, 20, 0)
    self.assertEqual(len(prev_list), 9)


if __name__ == "__main__":
  unittest.main()
