# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from functools import wraps

import sys
import math
import inspect

from bxemu.core import PortfolioManager
from bxemu.basic import Tick, Order, Trade
from bxemu.strategy import StrategyTemplate
from bxemu.constant import *


class BacktestAccount(PortfolioManager):
    
    def __init__(self, name):
        super(BacktestAccount, self).__init__(name)

    def preOrderCheck(fn):
        """
        先要做下单前的检查，检查通过才可以下单
        """
        @wraps(fn)
        def wrap(*args, **kwargs):
            """
            1.只能在策略里面调用
            2.下单数是否超过了持仓数
            """
            stack = inspect.stack()
            curClass = stack[1][0].f_locals["self"].__class__
            methodName = stack[1][0].f_code.co_name
            #print("I was called by {}.{}()".format(str(curClass), methodName))              
            #print(inspect.getmro(curClass))
            if methodName != "onTick":
                raise Exception("placeOrder方法只能在策略里面被调用")
            has = False
            for c in inspect.getmro(curClass):
                if c == StrategyTemplate:
                    has = True
                    break
            if not has:
                raise Exception("placeOrder方法只能在策略里面被调用")
            #=======================================================
            self, side, price, size = args
            assert side == DIRECTION_BUY or side == DIRECTION_SELL
            assert price > 0 and price <= 1000000
            assert size > 0 and size < 10000000
            #=======================================================
            return fn(*args, **kwargs)
        return wrap

    @preOrderCheck
    def placeOrder(self, side, price, size):
        order = Order.create(side, price, size, ORDER_TYPE_LIMIT)
        self.strategy.onOrder(order)
        #尝试成交
        self._deal(order, TRADE_TYPE_TAKER)
        return order.orderId

    def cancelOrder(self, orderId):
        #先要更新保证金占用
        if sys.version_info.major == 2:
            l = filter(lambda order:order.orderId==orderId, self.orderBook)
        else:
            l = list(filter(lambda order:order.orderId==orderId, self.orderBook))
        order = l[0]
        order.left = 0
        order.status = "Canceled"
        self.strategy.onOrder(order)

    def cancelAllOfOrders(self):
        for order in self.orderBook[:]:
            self.cancelOrder(order.orderId)

    def _deal(self, order, tradeType):
        if (order.side == DIRECTION_SELL and order.price <= self.lastFillPrice) or\
           (order.side == DIRECTION_BUY and order.price >= self.lastFillPrice):
            #获取本次可以成交的数量
            tradeVol = self._obtainTransactionVolume(order.left)
            #判断是否允许成交(比如说一成交就会导致仓位爆仓的情况就不允许成交)
            if self._allowTrade(order, tradeVol, self.lastFillPrice, self.lastMarkPrice, tradeType):
                #可以成交
                order.left -= tradeVol  #更新订单的已成交数量
                trade = Trade.create(order.side, tradeVol, self.lastFillPrice, order.type, order.size, order.left, order.price, order.orderId, tradeType)            
                self.strategy.onTrade(trade)
            else:   #不允许成交,取消这个订单
                order.left = 0
                order.status = "Trade not allowed, order canceled"
                self.strategy.onOrder(order)

    def _makeTrade(self):
        """
        撮合交易
        """
        for order in self.orderBook[:]:
            self._deal(order, TRADE_TYPE_MAKER)

    def processQuote(self, tupleQuote):
        """
        调用_makeTrade撮合订单
        调用策略的onTick
        """
        self.lastMarkPrice, self.lastFillPrice = tupleQuote
        #
        self._makeTrade()
        #
        tick = Tick.create(self.lastMarkPrice, self.lastFillPrice)
        self.strategy.onTick(tick)