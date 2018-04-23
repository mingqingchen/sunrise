import proto.stock_pb2 as stock_pb2

class PortfolioManager:
  def __init__(self):
    self.portfolio_ = stock_pb2.Portfolio()
    self.portfolio_.available_cash = 0
    self.portfolio_.balance = 0

  def deposit_money(self, sum_money):
    self.portfolio_.available_cash += sum_money
    self.portfolio_.balance += sum_money

  def get_available_cash(self):
    return self.portfolio_.available_cash
  
  def get_balance(self):
    return self.portfolio_.balance
  
  def update_balance(self, daily_all_stock_data):
    """Update the balance given current daily stock info based on close price.
    Args:
      daily_all_stock_data is a map of stock symbol to OneDayData
    """
    
    updated_balance = self.portfolio_.available_cash
    for stock_name in self.portfolio_.data.keys():
      if stock_name in daily_all_stock_data.keys():
        self.portfolio_.data[stock_name].current_price = daily_all_stock_data[stock_name].close
      updated_balance += self.portfolio_.data[stock_name].current_price * self.portfolio_.data[stock_name].volume
    self.portfolio_.balance = updated_balance
    return True
  
  def get_current_hold_symbol_list(self):
    return self.portfolio_.data.keys()
  
  def get_num_holding(self, symbol):
    """ Get volume of currently holded symbol. """
    return self.portfolio_.data[symbol].volume
  
  def get_buy_price(self, symbol):
    one_holding = self.portfolio_.data[symbol]
    return one_holding.purchase_cost / one_holding.volume
  
  def buy_stock(self, transaction):
    """ Buy amount of symbol stocks at price
    Return True for successful buy, 
    False may due to insufficient money
    """
    if transaction.amount==0:
      return True
    
    if transaction.amount < 0:
      print('Amount is smaller than zero. ')
      return False
    
    purchase_cost = transaction.amount * transaction.price
    required_money = purchase_cost + transaction.commission_fee
    print('Intended purchase: ', transaction)
    if required_money > self.portfolio_.available_cash:
      print('Failed to buy due to insufficient cash during buy transaction. ')
      print('Available cash: {0}'.format(self.portfolio_.available_cash))
      return False
    self.portfolio_.available_cash -= required_money
    symbol = transaction.symbol
    if symbol in self.portfolio_.data.keys():
      self.portfolio_.data[symbol].volume += transaction.amount
      self.portfolio_.data[symbol].purchase_cost += purchase_cost
    else:
      self.portfolio_.data[symbol].volume = transaction.amount
      self.portfolio_.data[symbol].purchase_cost = purchase_cost
    print('Transaction completed succesfully!')
    print('Available cash: {0}'.format(self.portfolio_.available_cash))
    return True

  def sell_stock(self, transaction):
    """ Buy amount of symbol stocks at price
    Return True for successful sell,
    False may due to insufficient amount.
    """
    if transaction.amount == 0:
      return True

    if transaction.amount < 0:
      print('Amount is smaller than zero. ')
      return False

    if transaction.symbol not in self.portfolio_.data.keys():
      print('Failed to sell since symbol is not in your portfolio. ', transaction.symbol)
      return False

    symbol = transaction.symbol
    if transaction.amount > self.portfolio_.data[symbol].volume:
      print('Failed to sell since amount is larger than your portfolio. ', transaction.symbol)
      return False

    cur_amount = self.portfolio_.data[symbol].volume
    self.portfolio_.data[transaction.symbol].purchase_cost *= ((cur_amount - transaction.amount) / float(cur_amount))
    self.portfolio_.data[transaction.symbol].volume -= transaction.amount
    self.portfolio_.available_cash += (transaction.amount * transaction.price)
    if self.portfolio_.data[transaction.symbol].volume == 0:
      del self.portfolio_.data[transaction.symbol]
    print('Successfully sell ', transaction)
    return True
