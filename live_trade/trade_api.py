import urllib
import os
import json

class TradeAPI:
  def __init__(self):
    self.refresh_token_file_ = './refresh_token.txt'
    self.access_token_file_ = './access_token.txt'
    self.temp_file_location_ = 'temp.txt'

    self.get_access_token_template_ = 'curl -X POST --header "Content-Type: application/x-www-form-urlencoded" -d "grant_type=refresh_token&refresh_token={0}&access_type=offline&code=&client_id=mingqing8%40AMER.OAUTHAP&redirect_uri=sunrsie" "https://api.tdameritrade.com/v1/oauth2/token" > {1}'
    self.get_history_price_template_ = 'curl -X GET --header "Authorization: " --header "Authorization: Bearer {0}" "https://api.tdameritrade.com/v1/marketdata/{1}/pricehistory?period=1&frequencyType=minute&frequency=1" > {2}'

  def get_refresh_token(self):
    fid = open(self.refresh_token_file_)
    lines = fid.readlines()
    fid.close()
    self.refresh_token_ = urllib.quote_plus(lines[0].replace('\n', ''))

  def get_new_access_token(self):
    get_access_token_command = self.get_access_token_template_.format(self.refresh_token_, self.temp_file_location_)
    os.system(get_access_token_command)
    response = json.load(open(self.temp_file_location_))
    if 'error' in response:
      print ('Could not get access token. Something is wrong !!!')
      return False
    else:
      self.refresh_token_ = response['refresh_token']
      self.access_token_ = response['access_token']
      fid = open(self.refresh_token_file_, 'w')
      fid.write(self.refresh_token_)
      fid.close()
      fid = open(self.access_token_file_, 'w')
      fid.write(self.access_token_)
      fid.close()
      print('Successfully Update Refresh and Access Token!')
      self.refresh_token_ = urllib.quote_plus(self.refresh_token_)
      return True

  def query_historical_price(self, symbol):
    query_string = self.get_history_price_template_.format(self.access_token_, symbol, self.temp_file_location_)
    os.system(query_string)
    response = dict()
    try:
      response = json.load(open(self.temp_file_location_))
    except ValueError:
      print('Error decoding json.')
      return False, response
    return True, response
