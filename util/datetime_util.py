import datetime

k_template_date = 20180405
k_template_timestamp = 1522935000
k_sec_per_day = 86400

def convert_int_to_day(input):
  '''Convert int format day from Yahoo finance to a more recognizable format.
    input format is: 1522330200
    output format is: 20180329
  '''
  day_diff = int((k_template_timestamp - input)/k_sec_per_day)
  return increment_day(k_template_date, -day_diff)
  
def convert_day_to_int(input):
  '''Reverse function of convert_int_to_day.'''
  template_date = int_to_date(k_template_date)
  input_date = int_to_date(input)
  day_delta = (input_date - template_date).days
  return k_template_timestamp + k_sec_per_day * day_delta

def get_today():
  return date_to_int(datetime.date.today())

def get_cur_time_int():
  cur_time = datetime.datetime.now()
  return cur_time.hour * 100 + cur_time.minute

def get_today_timestamp():
  return convert_day_to_int(get_today())

def time_to_int(input_time):
  return input_time.hour + input_time.minute

def int_to_time(input_time_val):
  hour = int(input_time_val / 100)
  minute = input_time_val - hour * 100
  return datetime.time(hour, minute, 0)

def add_minute_to_time(input_time_val, num_minute):
  h = int(input_time_val/100)
  m = input_time_val - h * 100
  m += num_minute
  while m >= 60:
    m -= 60
    h += 1
  return h * 100 + m

def next_minute(input_time_val):
  """ Given 1059, should return 1100 """
  return add_minute_to_time(input_time_val, 1)

def date_to_int(input_date):
  """ Given a date, returns a 8-digit int value of date. """
  return input_date.year*10000+input_date.month*100+input_date.day

def int_to_datetime(input_date_val, input_time_val):
  year = int(input_date_val/10000)
  input_date_val -= year*10000
  month = int(input_date_val/100)
  input_date_val -=month*100
  day = input_date_val

  hour = int(input_time_val/100)
  minute = input_time_val - hour * 100
  return datetime.datetime(year, month, day, hour, minute, 0)

def minute_diff(time_int_val1, time_int_val2):
  """ number of minute difference between two int time """
  t1 = int_to_time(time_int_val1)
  t2 = int_to_time(time_int_val2)
  return (t2.hour - t1.hour) * 60 + t2.minute - t1.minute

def convert_to_normalized_time(input_time, start_time, end_time):
  """ given a input_time in datetime format, and start_time and end_time in int format,
      return a float in the normalized value.
      e.g. 20180403 12:30 might return a value like 0403.83
  """
  result = input_time.month * 100 + input_time.day
  time_val = input_time.hour * 100 + input_time.minute
  ratio = float(minute_diff(time_val, start_time)) / minute_diff(end_time, start_time)
  return result + ratio

def int_to_date(input_date_val):
  """ Given a 8-digit int value of date, returns its datetime. """
  year = int(input_date_val/10000)
  input_date_val -= year*10000
  month = int(input_date_val/100)
  input_date_val -=month*100
  day = input_date_val
  return datetime.datetime(year, month, day)

def is_week_day(input_date_val):
  """ Given a 8-digit int value of date, returns whether it's a weekday. """
  weekday = int_to_date(input_date_val).weekday()
  # Might be confusing here, but 5 is Saturday and 6 is Sunday.
  return not((weekday == 5) or (weekday == 6))

def increment_day(input_date_val, n = 1):
  """ Given a 8-digit int value of date, return its next date. """
  date_ = int_to_date(input_date_val)
  if n>0:
    date_ += datetime.timedelta(days=n)
  else:
    date_ -= datetime.timedelta(days=-n)
  return date_to_int(date_)
