import sim_environment.simulation_pb2 as simulation_pb2

def check_transaction_correct(initial_deposit, transactions):
  """A function that checks transactions are correct. This can be used to test all trade strategies.
    Returns:
      remaining cash available (not the balance, note the diff occurs when some stocks are not sold at end)
  """
  amount = initial_deposit
  for transaction in transactions:
    if transaction.type == simulation_pb2.Transaction.BUY:
      amount = amount - transaction.amount * transaction.price - transaction.commission_fee
      print amount
      if amount <= 0:
        return -1
    elif transaction.type == simulation_pb2.Transaction.SELL:
      amount = amount + transaction.amount * transaction.price - transaction.commission_fee
      print amount
      if amount <= 0:
        return -1
  return amount

