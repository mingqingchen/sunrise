import datetime_util
import os
import unittest


class TestDataProvider(unittest.TestCase):
  def test_add_minute_to_time(self):
    self.assertEqual(datetime_util.add_minute_to_time(2354, 10), 4)
    self.assertEqual(datetime_util.add_minute_to_time(302, 100), 442)
    self.assertEqual(datetime_util.add_minute_to_time(302, 200), 622)
    self.assertEqual(datetime_util.add_minute_to_time(1059, 1), 1100)
    self.assertEqual(datetime_util.next_minute(1059), 1100)
    self.assertEqual(datetime_util.add_minute_to_time(1059, 3), 1102)

  def test_date_diff(self):
    self.assertEqual(datetime_util.date_diff(20181230, 20190105), 6)
    self.assertEqual(datetime_util.date_diff(20190105, 20181230), 6)
    self.assertEqual(datetime_util.date_diff(20190227, 20180227), 365)

  def test_minute_diff(self):
    self.assertEqual(datetime_util.minute_diff(1059, 1102), 3)
    self.assertEqual(datetime_util.minute_diff(1059, 1758), 419)
    self.assertEqual(datetime_util.minute_diff(2359, 0), 1)

  def test_convert_to_normalized_time(self):
    self.assertEqual(datetime_util.convert_to_normalized_time(20180305, 1100, 1000, 1200), 20180305.5)
    self.assertAlmostEqual(datetime_util.convert_to_normalized_time(20181003, 1200, 830, 1630), 20181003.4375)

  def test_is_weekday(self):
    self.assertTrue(datetime_util.is_week_day(20180803))
    self.assertFalse(datetime_util.is_week_day(20180804))
    self.assertTrue(datetime_util.is_week_day(20190104))
    self.assertFalse(datetime_util.is_week_day(20190105))
    self.assertFalse(datetime_util.is_week_day(20190106))

  def test_increment_day(self):
    self.assertEqual(datetime_util.increment_day(20181231, 1), 20190101)
    self.assertEqual(datetime_util.increment_day(20181031, 3), 20181103)
    self.assertEqual(datetime_util.increment_day(20180228, 50), 20180419)
    self.assertEqual(datetime_util.increment_day(20180228, 365), 20190228)
    self.assertEqual(datetime_util.increment_day(20190103, -5), 20181229)

if __name__ == "__main__":
  unittest.main()
