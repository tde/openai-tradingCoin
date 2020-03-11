from positionStore import PositionStore
from positionStore import Order
from positionStore import ActionType

store = PositionStore(initial_usd = 4000, initial_coins = 200, init_price = 20)
#print ("total balance = {}".format(store.calcTotalBalance()))

store.addOrder(Order(type = ActionType.SELL, price = 25, qty = 40))
store.addOrder(Order(type = ActionType.BUY, price = 24, qty = 1000))
store.show(20)

#1
#store.addOrder(Order(type = ActionType.SELL, price = 31, qty = 10))
#store.addOrder(Order(type = ActionType.BUY, price = 32, qty = 15))
#print ("remain = {}".format(store.calcRemainClose()))
#store.addOrder(Order(type = ActionType.BUY, price = 32, qty = 5))
#store.addOrder(Order(type = ActionType.SELL, price = 33, qty = 10))

#print ("profit = {}".format(store.calcAllProfit()))
#store.show()
"""
#2
o2 = Order(type = ActionType.BUY, price = 32.7, qty = 20)
store.addOrder(o2)
print ("profit = {}".format(store.calcAllProfit()))

#3
o3 = Order(type = ActionType.SELL, price = 35.7, qty = 50)
store.addOrder(o3)
store.show()

print ("all profit = {}".format(store.calcAllProfit()))
"""