# -*- coding: utf-8 -*-

from enum import Enum

"""
Профит считается гипотететически
при открытии ордера профит вычисляеся как если бы сразу продать с учетом спреда
"""

# комиссия (% / 100)
COMMISION_RATE = 0.001

# спред (% / 100)
SPREAD_RATE = 0.0005

"""
Возможные типы действия
"""
class ActionType(Enum):
  BUY = 0
  SELL = 1
  HOLD = 2

"""
Один order
  qty - это кол-во монет которые покупаются/продаются
"""
class Order:
  type = None
  price = 0
  qty = 0

  def __init__(self, type = None, price = None, qty = None, order = None):
    if (order != None):
      self.type = order.type
      self.price = order.price
      self.qty = qty
    else:
      self.type = type
      self.price = price
      self.qty = qty

  def getPriceWithSpread(self):
    k =  (1 + SPREAD_RATE) if self.type == ActionType.BUY else (1 - SPREAD_RATE)
    return self.price * k
  
  def calcAmount(self):
    return self.price * self.qty
  
  def calcAmountWithSpread(self):
    return self.getPriceWithSpread() * self.qty

  def toString(self): 
    return "type: {}, price: {}, qty: {}".format(self.type.name, self.price, self.qty)

"""
Одна позиция
"""
class Position:
  # позиция полностью закрыта
  isClosed = False

  # order на открытие должен быть только один
  openOrder = None

  # order'ов на закрытие может быть сколько угодно
  closeOrders = []

  # оставшееся кол-во для закрытия
  remainQtyForClose = 0

  # текущий профит только с учетом оредоров на закрытие
  currentProfit = 0

  # суммарная текущая комиссия
  totalCommission = 0

  def __init__(self, openOrder):
    assert openOrder.type == ActionType.BUY or openOrder.type == ActionType.SELL, 'wrong order type'
    self.openOrder = openOrder
    self.closeOrders = []
    self.isClosed = False
    self.remainQtyForClose = openOrder.qty
    self.totalCommission = self.openOrder.price * self.openOrder.qty * COMMISION_RATE

  # Добавить ордер на закрытие
  def addCloseOrder(self, closeOrder):
    assert self.isClosed == False, 'position already closed'
    assert not (closeOrder.type == self.openOrder.type), 'close and order has same type' 
    assert closeOrder.type == ActionType.BUY or closeOrder.type == ActionType.SELL, 'wrong order type'

    # вычислить кол-во для закрытия
    closeQty = self.remainQtyForClose if closeOrder.qty > self.remainQtyForClose else closeOrder.qty
    self.closeOrders.append(Order(order=closeOrder, qty=closeQty))
    closeOrder.qty -= closeQty

    # уменьшить оставшееся кол-ва для закрытия
    self.remainQtyForClose = self.remainQtyForClose - closeQty 
    
    # учесть комиссию
    self.totalCommission += closeOrder.price * closeQty * COMMISION_RATE

    # если больше нечего закрывать, то позиция закрыта
    if (self.remainQtyForClose <= 0.01):
      self.isClosed = True

    return closeOrder

  def calcProfit(self, closePrice):
    closeAmount = sum(o.calcAmountWithSpread() for o in self.closeOrders)

    # если позиция не закрыта, то надо создать фиктивный ордер для учета оставшейся части
    if (self.isClosed == False):
      type = ActionType.SELL if (self.openOrder.type == ActionType.BUY) else ActionType.BUY
      dummyOrder = Order(type = type, price = closePrice, qty = self.remainQtyForClose)
      dummyAmount = dummyOrder.calcAmountWithSpread()
    else:
      dummyAmount = 0

    # общая сумма закрытия
    closeAmount += dummyAmount

    if (self.openOrder.type == ActionType.BUY):
      result = closeAmount - self.openOrder.calcAmountWithSpread() 
    else:
      result = self.openOrder.calcAmountWithSpread() - closeAmount

    # для фиктивного оредра на учесть комиссию
    commision = self.totalCommission + dummyAmount * COMMISION_RATE

    return (result - commision)

  def show(self, index = None): 
    header = '== Position ==' if (index == None) else '== #{} =='.format(index)
    print (header)
    print ('isClosed: {}, remainQtyForClose: {}, profit: {}'.format(self.isClosed, self.remainQtyForClose, self.currentProfit))
    print ('openOrder: \n\t{}'.format(self.openOrder.toString()))
    print ('closeOrders:')
    for o in self.closeOrders: 
      print('\t{}'.format(o.toString()))
    print ("\n")

"""
Хранилище позиций
"""
class PositionStore:
  positions = []

  def __init__(self):
    self.positions = []

  def addOrder(self, order):
    # распределить сумму из order'a по всем отрытым позициям
    for p in self.positions:
      if (p.isClosed == False and p.openOrder.type != order.type):
        order = p.addCloseOrder(order)
        assert not order.qty < 0, 'error qty in order'
        if (order.qty == 0):
          break

    # не вся сумма распределан по позициям,то открыть новую
    if (order.qty > 0):
      p = Position(openOrder=order)
      self.positions.append(p)

  def calcAllProfit(self, closePrice):
    res = 0.0
    for p in self.positions:
      #print ("profit = {}".format(p.calcProfit(closePrice)))
      res += p.calcProfit(closePrice)

    return res
  
  def show(self):
    print('== ALL Positions ==')
    i = 0
    for p in self.positions:
      i += 1
      p.show(i)
