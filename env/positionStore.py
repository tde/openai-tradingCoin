# -*- coding: utf-8 -*-

from enum import Enum
import numpy as np

"""
Профит считается гипотететически
при открытии ордера профит вычисляеся как если бы сразу продать с учетом спреда
"""

# комиссия (% / 100)
COMMISION_RATE = 0.001

# спред (% / 100)
SPREAD_RATE = 0.0004

"""
Возможные типы действия
"""
class ActionType(Enum):
    BUY = 0
    SELL = 1
    HOLD = 2

"""
Один order
  qty - это кол-во usd/монет которые покупаются/продаются
"""
class Order:
    type = None
    price = 0
    qty = 0

    def __init__(self, type, price, qty, index = None):
        self.type = type
        self.price = price
        self.qty = qty
        self.index = index

    def getPriceWithSpread(self):
        k =  (1 + SPREAD_RATE) if self.type == ActionType.BUY else (1 - SPREAD_RATE)
        return self.price * k
  
    def calcAmount(self):
        return self.price * self.qty
  
    def calcAmountWithSpread(self):
        if (self.price == 0):
            print('price == 0')

        if (self.type == ActionType.BUY):
            return self.qty / self.getPriceWithSpread()
        else:
            return self.qty * self.getPriceWithSpread()
    

    def toString(self): 
        return "type: {}, price: {}, qty: {}".format(self.type.name, self.price, self.qty)

"""
 Позиция для одной монеты
"""
class PositionStore:
    # все order'a
    orders = []

    # сколько на данный момент есть USD
    current_usd = 0

    # сколько на данный момент есть монет
    current_coins = 0

    # начальный баланс пересчитанный в USD
    initial_total_balance = 0

    # индекс в резалтсете на которых была последняя покупка/продажа
    last_buy_index = 0
    last_sell_index = 0

    def __init__(self, initial_usd, initial_coins, initial_price):
        self.current_usd = initial_usd
        self.current_coins = initial_coins
        self.initial_price = initial_price
        self.initial_total_balance = initial_usd + initial_price * initial_coins

        # максимальное увеличение активов в два раза на заданном интервале удержания позиции
        self.max_usd = 2 * (initial_usd + initial_coins * initial_price)
        self.max_coins = 2 * (initial_coins + initial_usd / initial_price)

    # Добавить ордер на закрытие
    def addOrder(self, order):
        if (order.price == 0):
            print ('order price == 0')

        # штраф за слишком быструю "обратную" сделку
        if (order.type == ActionType.BUY):
            diff_index = (order.index - self.last_sell_index) if self.last_sell_index > 0 else 10000
            self.last_buy_index = order.index
        elif (order.type == ActionType.SELL):
            diff_index = (order.index - self.last_buy_index) if self.last_buy_index > 0 else 10000
            self.last_sell_index = order.index

        reduce_coef = 2 * np.arctan(diff_index * 0.2) / np.pi

        # это покупка монет за USD
        if (order.type == ActionType.BUY):
            self.current_usd -= order.qty
            self.current_coins += order.calcAmountWithSpread() * (1 - COMMISION_RATE) * reduce_coef
        # это продажа монет 
        else:
            self.current_usd += order.calcAmountWithSpread() * (1 - COMMISION_RATE) * reduce_coef
            self.current_coins -= order.qty

        self.orders.append(order)

    def getLastOrder(self): 
        return self.orders[-1]

    # вычислить суммарный баланс в USD
    def calcTotalBalance(self, current_price):
        price = current_price if current_price != None else self.initial_price
        dummy_order = Order(type = ActionType.SELL, price = price, qty = self.current_coins, index = 0)
        return self.current_usd + dummy_order.calcAmountWithSpread() * (1 - COMMISION_RATE)

    def calcProfit(self, current_price):
        return self.calcTotalBalance(current_price) - self.initial_total_balance

    def show(self, current_price): 
        profit = self.calcTotalBalance(current_price) - self.initial_total_balance
        print ('Orders count: {}, current_usd: {}, current_coins: {}, profit = {}'
            .format(len(self.orders), self.current_usd, self.current_coins, profit))

    def showOrders(self): 
        for o in self.orders:
            print (f'\tindex = {o.index}, type = {o.type.name}, price = {o.price}, qty = {o.qty}')