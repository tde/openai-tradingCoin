from positionStore import PositionStore
from positionStore import Order
from positionStore import ActionType

store = PositionStore()

#1
o1 = Order(type = ActionType.BUY, price = 31.2, qty = 10)
store.addOrder(o1)
print ("profit = {}".format(store.calcAllProfit()))
#store.show()

#2
o2 = Order(type = ActionType.BUY, price = 32.7, qty = 20)
store.addOrder(o2)
print ("profit = {}".format(store.calcAllProfit()))

#3
o3 = Order(type = ActionType.SELL, price = 35.7, qty = 50)
store.addOrder(o3)
store.show()

print ("all profit = {}".format(store.calcAllProfit()))