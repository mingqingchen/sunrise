import os
import matplotlib.pyplot as plt
import util.data_provider as data_provider
import proto.stock_pb2 as stock_pb2
import numpy as np

k_data_folder = './data/intra_day/'
class SimulationHtmlReport:
  def __init__(self, sim_name, transactions, datetime_list, balances, skip_details=True):
    self.sim_name_ = sim_name
    self.transactions_ = transactions
    self.datetime_list_ = datetime_list
    self.balances_ = balances
    self.skip_details_ = skip_details
    self.highlight_revenue_threshold_ = 500
  
  def __export_balance_figure(self, imgpath):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    ax.plot(self.datetime_list_, self.balances_)
    min_date = np.min(self.datetime_list_)
    max_date = np.max(self.datetime_list_)
    step = max(1, int((max_date - min_date) / 10))
    ax.set_xticks(np.arange(np.min(self.datetime_list_), np.max(self.datetime_list_), step))
    ax.grid()
    plt.savefig(imgpath)
    plt.clf()


  def __export_to_html(self, file_path, day_symbol_transaction_index_dict):
    fid = open(file_path, 'w')
    
    fid.write('<!DOCTYPE html>\n')
    fid.write('<html>\n')
    fid.write('<head>\n')
    fid.write('<title> Report for Simulation {0} </title>\n'.format(self.sim_name_))
    fid.write('<style> \
    table, th, td \
    { \
      border: 1px solid black; \
      border-collapse: collapse; \
    } \
    th, td \
    { \
      padding: 5px; \
      text-align: left; \
    } \
    </style>')
    fid.write('</head>\n')
    fid.write('<body>\n')
    
    fid.write('<p>Overall balance change</p>\n')
    fid.write('<img src="./img/balance.png">\n')

    fid.write('<p>Total number of transactions: {0}</p>\n'.format(len(self.transactions_)))

    transaction_dict = dict()
    total_revenue = 0
    fid.write('<p><table>\n')
    fid.write('<caption> All transactions </caption>\n')
    fid.write('<tr><th>Symbol</th><th>buyvolume</th><th>sellvolume</th><th>buyprice</th><th>sellprice</th>'
              '<th>buydate</th><th>selldate</th><th>buytime</th><th>selltime</th>'
              '<th>revenue</th></tr>\n')
    for transaction in self.transactions_:
      if transaction.type == stock_pb2.Transaction.BUY:
         transaction_dict[transaction.symbol] = transaction
      else:
        buy_trans = transaction_dict[transaction.symbol]
        revenue = (transaction.price - buy_trans.price) * transaction.amount - buy_trans.commission_fee - \
                  transaction.commission_fee
        total_revenue += revenue

        table_row_tmpl = '<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>\
          {6}</td><td>{7}</td><td>{8}</td>'

        if revenue > self.highlight_revenue_threshold_:
          table_row_tmpl+='<td bgcolor=green>{9}</td></tr>\n'
        elif revenue < -self.highlight_revenue_threshold_:
          table_row_tmpl += '<td bgcolor=red>{9}</td></tr>\n'
        else:
          table_row_tmpl += '<td>{9}</td></tr>\n'
        fid.write(table_row_tmpl.format(
          transaction.symbol, buy_trans.amount, transaction.amount, round(buy_trans.price, 2),
          round(transaction.price, 2),
          buy_trans.date, transaction.date, buy_trans.time, transaction.time, round(revenue, 2)
        ))
        transaction_dict[transaction.symbol].amount -= transaction.amount
        if transaction_dict[transaction.symbol].amount == 0:
          del transaction_dict[transaction.symbol]
    fid.write('</table></p>\n')
    fid.write('Total revenue: {0}\n'.format(total_revenue))

    if self.skip_details_:
      return

    for date_val in day_symbol_transaction_index_dict.keys():
      for symbol in day_symbol_transaction_index_dict[date_val].keys():
        fid.write('Trade on {0} for {1}</br>\n'.format(date_val, symbol))
        for transaction in day_symbol_transaction_index_dict[date_val][symbol]:
          if transaction.type == stock_pb2.Transaction.BUY:
            fid.write('Buy {0} volumes at {1} {2} on price {3} </br>\n'.format(transaction.amount, transaction.date,
                                                                               transaction.time,
                                                                               round(transaction.price, 2)))
          else:
            fid.write('Sell {0} volumes at {1} {2} on price {3} </br>\n'.format(transaction.amount, transaction.date,
                                                                                transaction.time,
                                                                                round(transaction.price, 2)))
        img_filename = '{0}_{1}.png'.format(date_val, symbol)
        fid.write('<img src="./img/{0}"></p>\n'.format(img_filename))
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

    # export HTML
    html_path = os.path.join(folder, 'index.html')
    day_symbol_transaction_index_dict = dict()

    # go through all transactions
    if not self.skip_details_:
      for transaction in self.transactions_:
        if transaction.date not in day_symbol_transaction_index_dict:
          day_symbol_transaction_index_dict[transaction.date] = dict()
        if transaction.symbol not in day_symbol_transaction_index_dict[transaction.date]:
          day_symbol_transaction_index_dict[transaction.date][transaction.symbol] = []
        day_symbol_transaction_index_dict[transaction.date][transaction.symbol].append(transaction)
    self.__export_to_html(html_path, day_symbol_transaction_index_dict)

    if self.skip_details_:
      return

    # export figures
    dp = data_provider.DataProvider(k_data_folder, False)
    for date_val in day_symbol_transaction_index_dict.keys():
      for symbol in day_symbol_transaction_index_dict[date_val].keys():
        img_path = os.path.join(img_folder, '{0}_{1}.png'.format(date_val, symbol))
        dp.load_one_symbol(date_val, symbol)
        one_stock_data = dp.get_one_symbol_data(symbol)
        dp.export_one_symbol_one_day(symbol, one_stock_data, img_path, transactions = day_symbol_transaction_index_dict[date_val][symbol])




