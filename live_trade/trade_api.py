import urllib
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

k_client_id = 'MINGQING999%40AMER.OAUTHAP'
k_redirect_uri = 'http://www.google.com'

class TradeAPI:
  def __init__(self):
    self.refresh_token_file_ = './refresh_token.txt'
    self.access_token_file_ = './access_token.txt'



    self.get_access_token_url = 'https://api.tdameritrade.com/v1/oauth2/token'
    self.get_access_token_body = 'grant_type=refresh_token&refresh_token=%s&access_type=offline&code=&client_id=%s%40AMER.OAUTHAP&redirect_uri=%s' % (
      '{0}', k_client_id, k_redirect_uri)

    self.get_history_price_template_ = 'https://api.tdameritrade.com/v1/marketdata/{0}/pricehistory?period=1&frequencyType=minute&frequency=1'
    self.real_time_quotes_template_ = 'https://api.tdameritrade.com/v1/marketdata/quotes?apikey={0}&symbol={1}'

    self.get_account_template_ = 'https://api.tdameritrade.com/v1/accounts'

    self.http = urllib3.PoolManager()

  def get_refresh_token(self):
    fid = open(self.refresh_token_file_)
    lines = fid.readlines()
    fid.close()
    self.refresh_token_ = urllib.quote_plus(lines[0].replace('\n', ''))

  def get_new_access_token(self):
    query_body = self.get_access_token_body.format(self.refresh_token_)
    query_response = self.http.request('POST',
                                       self.get_access_token_url,
                                       headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                       body=query_body)
    response = json.loads(query_response.data.decode('utf-8'))

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

  def get_account_info(self):
    query_header_authorization = 'Bearer {0}'.format(self.access_token_)
    query_response = self.http.request('GET', self.get_account_template_, headers={'Authorization': query_header_authorization})
    try:
      response = json.loads(query_response.data.decode('utf-8'))[0]
      if 'error' in response:
        print('Failed to get account info. Something is wrong!!!')
        return False
      self.account_id_ = response['securitiesAccount']['accountId']
      self.is_day_trader_ = response['securitiesAccount']['isDayTrader']
      self.cash_available_for_trading_ = response['securitiesAccount']['currentBalances']['cashAvailableForTrading']      
    except ValueError:
      print('Error decoding json during querying account info.')
      return False
    return True

  def query_historical_price(self, symbol):
    """ Get historical price of a symbol. Large time delay. Typically only able to query after market close for a day. """
    query_request = self.get_history_price_template_.format(symbol)
    query_header_authorization = 'Bearer {0}'.format(self.access_token_)
    query_response = self.http.request('GET', query_request, headers={'Authorization': query_header_authorization})
    try:
      response = json.loads(query_response.data.decode('utf-8'))
    except ValueError:
      print('Error decoding json.')
      return False, response
    return True, response

  def query_updated_quotes(self, symbol_list):
    """ Given a symbol_list, get the real time updated quotes. """
    symbol_str = ''
    for symbol in symbol_list:
      if symbol_str!='':
        symbol_str += '%2C'
      symbol_str += symbol

    query_request = self.real_time_quotes_template_.format(k_client_id, symbol_str)
    query_response = self.http.request('GET', query_request)
    query_content = json.loads(query_response.data.decode('utf-8'))
    return True, query_content

