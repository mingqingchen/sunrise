import os
import matplotlib.pyplot as plt
import data_provider_png_exporter
import sim_environment.simulation_pb2 as simulation_pb2
import datetime_util
import numpy as np

class SimulationHtmlReport:
  def __init__(self, sim_name, transactions, datetime_list, balances, skip_details=True):
    self.sim_name_ = sim_name
    self.transactions_ = transactions
    self.datetime_list_ = datetime_list
    self.balances_ = balances
    self.skip_details_ = skip_details
    self.highlight_revenue_threshold_ = 500
  
  def _export_balance_figure(self, imgpath):
    fig = plt.figure(figsize=[8, 4])
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(self.datetime_list_, self.balances_)
    min_date = np.min(self.datetime_list_)
    max_date = np.max(self.datetime_list_)
    # step = max(1, int((max_date - min_date) / 10))
    # ax.set_xticks(np.arange(np.min(self.datetime_list_), np.max(self.datetime_list_), step))
    ax.grid()
    plt.savefig(imgpath)
    plt.clf()


  def _export_to_html(self, file_path, day_symbol_transaction_index_dict):
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

    fid.write('<p><table>\n')
    fid.write('<caption> All transactions </caption>\n')
    fid.write('<tr><th>Symbol</th><th>volume</th><th>price</th>'
              '<th>date</th><th>time</th><th>Balance</th>'
              '</tr>\n')

    balance_index = 0
    for transaction in self.transactions_:
      table_row_tmpl = '<tr><td style="background-color:{0}">{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td></tr>'
      tr_color = 'red'
      if transaction.type == simulation_pb2.Transaction.SELL:
        tr_color = 'blue'

      transaction_time = datetime_util.int_to_datetime(transaction.date, transaction.time)
      while self.datetime_list_[balance_index] < transaction_time:
        balance_index+=1
      current_balance = self.balances_[balance_index]

      fid.write(table_row_tmpl.format(tr_color,
        transaction.symbol, transaction.amount, round(transaction.price, 2),
        transaction.date, transaction.time, current_balance
      ))
    fid.write('</table></p>\n')

    if self.skip_details_:
      return

    for date_val in day_symbol_transaction_index_dict.keys():
      for symbol in day_symbol_transaction_index_dict[date_val].keys():
        fid.write('Trade on {0} for {1}</br>\n'.format(date_val, symbol))
        for transaction in day_symbol_transaction_index_dict[date_val][symbol]:
          if transaction.type == simulation_pb2.Transaction.BUY:
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

  def export(self, output_folder, dp):
    if not os.path.isdir(output_folder):
      os.makedirs(output_folder)
    img_folder = os.path.join(output_folder, 'img/')
    if not os.path.isdir(img_folder):
      os.makedirs(img_folder)
    
    # export balance figure
    balance_change_fig_path = os.path.join(img_folder, 'balance.png')
    self._export_balance_figure(balance_change_fig_path)

    # export HTML
    html_path = os.path.join(output_folder, 'index.html')
    day_symbol_transaction_index_dict = dict()

    # go through all transactions
    if not self.skip_details_:
      for transaction in self.transactions_:
        if transaction.date not in day_symbol_transaction_index_dict:
          day_symbol_transaction_index_dict[transaction.date] = dict()
        if transaction.symbol not in day_symbol_transaction_index_dict[transaction.date]:
          day_symbol_transaction_index_dict[transaction.date][transaction.symbol] = []
        day_symbol_transaction_index_dict[transaction.date][transaction.symbol].append(transaction)
    self._export_to_html(html_path, day_symbol_transaction_index_dict)

    if self.skip_details_:
      return

    # export figures
    png_exporter = data_provider_png_exporter.DataProviderPngExporter()
    for date_val in day_symbol_transaction_index_dict.keys():
      for symbol in day_symbol_transaction_index_dict[date_val].keys():
        img_path = os.path.join(img_folder, '{0}_{1}.png'.format(date_val, symbol))
        dp.load_one_symbol_data(date_val, symbol)
        one_stock_data = dp.get_one_symbol_data(symbol)
        png_exporter.export_one_symbol_one_day(symbol, one_stock_data, img_path, transactions=day_symbol_transaction_index_dict[date_val][symbol])




