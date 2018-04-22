import matplotlib.pyplot as plt

class DisplayUtil:
  def __init__(self):
    self.transcation_map_ = dict()
    self.datetime_list_map_ = dict()
    self.balance_map_ = dict()
  
  def add_one_simulation_result(self, sim_name, transactions, datetime_list, balances):
    self.transcation_map_[sim_name] = transactions
    self.datetime_list_map_[sim_name] = datetime_list
    self.balance_map_[sim_name] = balances

  def display(self):
    plot_handles = []
    color_index = 0
    for sim_name in self.transcation_map_:
      one_handle, = plt.plot(self.datetime_list_map_[sim_name], self.balance_map_[sim_name])
      plot_handles.append(one_handle)
    plt.legend(plot_handles, self.transcation_map_.keys())
    plt.grid()
    plt.show()
    plt.clf()
