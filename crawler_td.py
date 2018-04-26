import os
import pandas as pd
import proto.stock_pb2 as stock_pb2
import util.datetime_util as datetime_util

import pdb

fid = open('token.txt')
lines = fid.readlines()
fid.close()

query_string = lines[0]

query_url = 'https://api.tdameritrade.com/v1/marketdata/{0}/pricehistory?period=1&frequencyType=minute&frequency=1'

symbol = 'ISRG'

local_file_name = './temp.txt'
query_string = lines[0] + ' "' + query_url.format(symbol) + '" > {0}'.format(local_file_name)

os.system(query_string)

fid = open(local_file_name)
lines = fid.readlines()
fid.close()

one_symbol_data = stock_pb2.OneIntraDayData()
for line in lines:
  if '"candles":' in line:
    start_index = line.index('[')
    finish_index = line.index(']')
    line = line[start_index + 1 : finish_index]
    split_lines = line.split('},')
   
    one_symbol_data.symbol = symbol
    one_symbol_data.date = datetime_util.get_today()
    one_symbol_data.resolution = 1
    
    for timeslot_line in split_lines:
      timeslot_line = timeslot_line.replace('{', '')
      timeslot_line = timeslot_line.replace('}', '')
      split_content = timeslot_line.split(',')
      
      one_time_data = one_symbol_data.data.add()
      for content in split_content:
        kv_pair = content.split(':')
        if len(kv_pair)!=2:
          continue
        str_key = kv_pair[0].replace('"', '')
        str_val = kv_pair[1]
        if str_key == 'open':
          one_time_data.open = float(str_val)
        elif str_key == 'high':
          one_time_data.high = float(str_val)
        elif str_key == 'close':
          one_time_data.close = float(str_val)
        elif str_key == 'low':
          one_time_data.low = float(str_val)
        elif str_key == 'volume':
          one_time_data.volume = int(str_val)
        elif str_key == 'datetime':
          cl_time = pd.to_datetime(int(str_val), unit = 'ms')
          cl_time = cl_time.tz_localize('UTC').tz_convert('America/Los_Angeles')
          one_time_data.time_val = cl_time.hour * 100 + cl_time.minute

print one_symbol_data

