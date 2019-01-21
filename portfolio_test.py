import sim_environment.portfolio as portfolio
import sim_environment.simulation_pb2 as simulation_pb2
import os
import util.stock_pb2 as stock_pb2
import unittest


class TestPortfolio(unittest.TestCase):
  def test_buy_sell(self):
    # First, test balance is correct after depositing $2000
    p = portfolio.PortfolioManager()
    p.deposit_money(2000)
    self.assertEqual(p.get_available_cash(), 2000)
    self.assertEqual(p.get_balance(), 2000)

    # test you cannot buy 4200 value stuff with $2000
    t = simulation_pb2.Transaction()
    t.type = simulation_pb2.Transaction.BUY
    t.symbol = 'dummy'
    t.amount = 3
    t.price = 1400
    t.commission_fee = 7
    t.date = 20181114
    t.time = 630

    self.assertFalse(p.buy_stock(t))
    self.assertEqual(p.get_available_cash(), 2000)
    self.assertEqual(p.get_balance(), 2000)

    # test you can buy 3 volume of $300 stock
    t.price = 300

    self.assertTrue(p.buy_stock(t))
    self.assertEqual(p.get_available_cash(), 1093)
    self.assertEqual(p.get_balance(), 1993)

    self.assertTrue(p.if_symbol_is_in_holding('dummy'))
    self.assertFalse(p.if_symbol_is_in_holding('fancy'))
    self.assertTrue(p.get_num_holding('dummy'), 3)
    self.assertListEqual(p.get_current_hold_symbol_list(), ['dummy'])

    # test you can not buy another $1500 value
    t.symbol = 'fancy'
    t.amount = 5
    t.price = 300
    t.date = 20181115
    self.assertFalse(p.buy_stock(t))
    self.assertEqual(p.get_available_cash(), 1093)
    self.assertEqual(p.get_balance(), 1993)

    # test you can buy another 5 volume of $200 stock
    t.price = 200
    self.assertTrue(p.buy_stock(t))
    self.assertEqual(p.get_available_cash(), 86)
    self.assertEqual(p.get_balance(), 1986)

    self.assertTrue(p.if_symbol_is_in_holding('dummy'))
    self.assertTrue(p.if_symbol_is_in_holding('fancy'))
    self.assertTrue(p.get_num_holding('dummy'), 3)
    self.assertTrue(p.get_num_holding('fancy'), 5)
    self.assertSetEqual(set(p.get_current_hold_symbol_list()), {'fancy', 'dummy'})

    # test balance is correct after update stock price
    dummy_data = stock_pb2.OneTimeSlotData()
    dummy_data.open = 380
    dummy_data.close = 385
    dummy_data.volume = 100
    fancy_data = stock_pb2.OneTimeSlotData()
    fancy_data.open = 250
    fancy_data.close = 252
    fancy_data.volume = 5000
    update_dict = {'dummy': dummy_data, 'fancy': fancy_data}
    p.update_balance(update_dict)
    self.assertEqual(p.get_available_cash(), 86)
    self.assertEqual(p.get_balance(), 86 + 380 * 3 + 250 * 5)

    # test you cannot sell invalid transaction, or volume more than available amount
    t.type = simulation_pb2.Transaction.BUY
    t.amount = 10
    t.price = 500
    self.assertFalse(p.sell_stock(t))

    t.type = simulation_pb2.Transaction.SELL
    self.assertFalse(p.sell_stock(t))

    self.assertEqual(p.get_available_cash(), 86)
    self.assertEqual(p.get_balance(), 86 + 380 * 3 + 250 * 5)

    # test sell 2 volumes of "fancy"
    t.amount = 2
    self.assertTrue(p.sell_stock(t))
    self.assertEqual(p.get_available_cash(), 86 - 7 + 2 * 500)
    self.assertEqual(p.get_balance(), 86 - 7 + 380 * 3 + 250 * 3 + 2 * 500)
    self.assertTrue(p.get_num_holding('dummy'), 3)
    self.assertTrue(p.get_num_holding('fancy'), 3)
    self.assertSetEqual(set(p.get_current_hold_symbol_list()), {'fancy', 'dummy'})

    # test sell another 2 volumes of "fancy"
    t.amount = 2
    t.price = 700
    self.assertTrue(p.sell_stock(t))
    self.assertEqual(p.get_available_cash(), 86 - 7 - 7 + 2 * 500 + 2 * 700)
    self.assertEqual(p.get_balance(), 86 - 7 - 7 + 380 * 3 + 250 + 2 * 500 + 2 * 700)
    self.assertTrue(p.get_num_holding('dummy'), 3)
    self.assertTrue(p.get_num_holding('fancy'), 1)
    self.assertSetEqual(set(p.get_current_hold_symbol_list()), {'fancy', 'dummy'})

    # test you cannot sell another 2 volumes of "fancy"
    t.amount = 2
    t.price = 700
    self.assertFalse(p.sell_stock(t))

    # test sell remaining of "fancy"
    t.amount = 1
    t.price = 100
    self.assertTrue(p.sell_stock(t))
    self.assertEqual(p.get_available_cash(), 86 - 7 - 7 - 7 + 2 * 500 + 2 * 700 + 100)
    self.assertEqual(p.get_balance(), 86 - 7 - 7 - 7 + 380 * 3 + 100 + 2 * 500 + 2 * 700)
    self.assertTrue(p.get_num_holding('dummy'), 3)
    self.assertSetEqual(set(p.get_current_hold_symbol_list()), {'dummy'})








if __name__ == "__main__":
  unittest.main()
