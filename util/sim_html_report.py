import os
import matplotlib.pyplot as plt
import util.data_provider as data_provider
import proto.stock_pb2 as stock_pb2

k_data_folder = './data/intra_day/'
class SimulationHtmlReport:
  def __init__(self, sim_name, transactions, datetime_list, balances):
    self.sim_name_ = sim_name
    self.transactions_ = transactions
    self.datetime_list_ = datetime_list
    self.balances_ = balances
  
  def __export_balance_figure(self, imgpath):
    plt.plot(self.datetime_list_, self.balances_)
    plt.grid()
    plt.savefig(imgpath)
    plt.clf()


  def __export_to_html(self, file_path, day_symbol_transaction_index_dict):
    fid = open(file_path, 'w')
    
    fid.write('<!DOCTYPE html>\n')
    fid.write('<html>\n')
    fid.write('<head>\n')
    fid.write('<title> Report for Simulation {0} </title>\n'.format(self.sim_name_))
    fid.write('</head>\n')
    fid.write('<body>\n')
    
    fid.write('<p>Overall balance change</p>\n')
    fid.write('<img src="./img/balance.png">\n')

    fid.write('<p>Total number of transactions: {0}</br>\n'.format(len(self.transactions_)))
    
    total_revenue = 0
    for date_val in day_symbol_transaction_index_dict.keys():
      for symbol in day_symbol_transaction_index_dict[date_val].keys():
        revenue = 0
        revenue_comission = 0
        for transaction in day_symbol_transaction_index_dict[date_val][symbol]:
          if transaction.type == stock_pb2.Transaction.BUY:
            fid.write('Buy {0} volumes at {1} on price {2} </br>\n'.format(transaction.amount, transaction.time, transaction.price))
            revenue -= transaction.amount * transaction.price
            revenue_comission -= transaction.amount * transaction.price
            revenue_comission -= transaction.commission_fee
          else:
            fid.write('Sell {0} volumes at {1} on price {2} </br>\n'.format(transaction.amount, transaction.time, transaction.price))
            revenue += transaction.amount * transaction.price
            revenue_comission += transaction.amount * transaction.price
            revenue_comission -= transaction.commission_fee
        fid.write('Revenue: {0} </br>\n'.format(revenue))
        fid.write('Revenue after comission: {0} </br>\n'.format(revenue_comission))
        img_filename = '{0}_{1}.png'.format(date_val, symbol)
        fid.write('Trade on {0} for {1}</br>\n'.format(date_val, symbol))
        fid.write('<img src="./img/{0}"></p>\n'.format(img_filename))
        total_revenue += revenue_comission
    fid.write('<p> Total revenue: {0} </p>'.format(total_revenue))
    fid.write('</body>\n')
    fid.write('</html>\n')
    fid.close()

  def export(self, folder):
    if not os.path.isdir(folder):
      os.makedirs(folder)
    img_folder = os.path.join(folder, 'img/')
    if not os.path.isdir(img_folder):
      os.makedirs(img_folder)
    
    # export balance figure
    balance_change_fig_path = os.path.join(img_folder, 'balance.png')
    self.__export_balance_figure(balance_change_fig_path)

    # go through all transactions
    day_symbol_transaction_index_dict = dict()
    for transaction in self.transactions_:
      if transaction.date not in day_symbol_transaction_index_dict:
        day_symbol_transaction_index_dict[transaction.date] = dict()
      if transaction.symbol not in day_symbol_transaction_index_dict[transaction.date]:
        day_symbol_transaction_index_dict[transaction.date][transaction.symbol] = []
      day_symbol_transaction_index_dict[transaction.date][transaction.symbol].append(transaction)

    # export figures
    dp = data_provider.DataProvider(k_data_folder)
    for date_val in day_symbol_transaction_index_dict.keys():
      for symbol in day_symbol_transaction_index_dict[date_val].keys():
        img_path = os.path.join(img_folder, '{0}_{1}.png'.format(date_val, symbol))
        dp.load_one_symbol(date_val, symbol)
        one_stock_data = dp.get_one_symbol_data(symbol)
        dp.export_one_symbol_one_day(symbol, one_stock_data, img_path, transactions = day_symbol_transaction_index_dict[date_val][symbol])

    # export HTML
    html_path = os.path.join(folder, 'index.html')
    self.__export_to_html(html_path, day_symbol_transaction_index_dict)


