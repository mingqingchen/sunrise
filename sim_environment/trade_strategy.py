k_commission_fee = 7.0

class TradeStrategy:
  """ Intra-day trading strategy. """
  def run_minute_trade_strategy(self, data_manager, cur_time, portfolio):
    return []

  def update_date(self, date_int_val, data_manager):
    """ This provides needed operations when a new day is updated. """
    self.date_int_val_ = date_int_val
    return
