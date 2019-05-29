# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import sys
try:
    reload         # Python 2
    reload(sys)
    sys.setdefaultencoding('utf8')
except NameError:  # Python 3
    from importlib import reload
    reload(sys)

import datetime
import sqlite3

import pandas as pd

from bxemu.constant import *
from bxemu.bitmexaccount import BacktestAccount
from bxemu.strategy import StrategyTemplate
import bxemu.util as util
import rootpath


class settings():pass
# How many pairs of buy/sell orders to keep open
settings.ORDER_PAIRS = 6
# ORDER_START_SIZE will be the number of contracts submitted on level 1
# Number of contracts from level 1 to ORDER_PAIRS - 1 will follow the function
# [ORDER_START_SIZE + ORDER_STEP_SIZE (Level -1)]
settings.ORDER_START_SIZE = 10
settings.ORDER_STEP_SIZE = 10
# Distance between successive orders, as a percentage (example: 0.005 for 0.5%)
settings.INTERVAL = 0.002
# If you exceed a position limit, the bot will log and stop quoting that side.
settings.MAX_POSITION = 1000
#
settings.RELIST_INTERVAL = settings.INTERVAL*5


class MarketMakingStrategy(StrategyTemplate):
    """
    简单做市商策略
    """

    def __init__(self, pm):
        super(MarketMakingStrategy, self).__init__(pm)

    def onInit(self):
        """初始化策略"""
        #基准价格
        self.benchmark = EMPTY_FLOAT

    def long_position_limit_exceeded(self):
        """Returns True if the position limit is exceeded"""
        if self.pm.position.isHolding() and self.pm.position.side == DIRECTION_BUY:
            return self.pm.position.size >= settings.MAX_POSITION
        else:
            return False

    def short_position_limit_exceeded(self):
        """Returns True if the position limit is exceeded"""
        if self.pm.position.isHolding() and self.pm.position.side == DIRECTION_SELL:
            return self.pm.position.size >= settings.MAX_POSITION
        else:
            return False

    def get_price_offset(self, index, tick):
        """Given an index (1, -1, 2, -2, etc.) return the price for that side of the book.
           Negative is a buy, positive is a sell."""
        start_position = tick.lastFillPrice
        return util.toNearest(start_position * (1 + settings.INTERVAL) ** index, 0.5)

    def prepare_order(self, index, tick):
        """Create an order object."""
        quantity = settings.ORDER_START_SIZE + ((abs(index) - 1) * settings.ORDER_STEP_SIZE)
        price = self.get_price_offset(index, tick)
        return {'price': price, 'qty': quantity}

    def converge_orders(self, buy_orders, sell_orders, tick):
        if self.benchmark == EMPTY_FLOAT or abs(tick.lastFillPrice/self.benchmark-1) > settings.RELIST_INTERVAL:
            #先取消所有存在的订单
            self.pm.cancelAllOfOrders()            
            #开始下多单
            for order in buy_orders:
                self.pm.placeOrder(DIRECTION_BUY, order['price'], order['qty'])
            #开始下空单
            for order in sell_orders:
                self.pm.placeOrder(DIRECTION_SELL, order['price'], order['qty'])            
            #设置新的基准价格
            self.benchmark = tick.lastFillPrice

    def onTick(self, tick):
        """收到行情TICK推送"""
        try:
            buy_orders = []
            sell_orders = []
            # Create orders from the outside in. This is intentional - let's say the inner order gets taken;
            # then we match orders from the outside in, ensuring the fewest number of orders are amended and only
            # a new order is created in the inside. If we did it inside-out, all orders would be amended
            # down and a new order would be created at the outside.
            for i in reversed(range(1, settings.ORDER_PAIRS + 1)):
                if not self.long_position_limit_exceeded():
                    buy_orders.append(self.prepare_order(-i, tick))
                if not self.short_position_limit_exceeded():
                    sell_orders.append(self.prepare_order(i, tick))
            #准备下单
            self.converge_orders(buy_orders, sell_orders, tick)
        except Exception as e:
            print(e)

    def onOrder(self, order):
        """收到委托变化推送"""
        print("Order status: " + order.status)

    def onTrade(self, trade):
        """收到成交推送"""
        pass


class BacktestBitMEXMarket(object):
    
    def __init__(self):
        pass
    
    def run(self):
        """
        1.创建账户实例，可多个
        2.为每个账户实例绑定对应的策略
        3.从实时数据源/数据库/模拟数据源等读取行情数据
        4.循环调用processQuote
        """
        
        self.account = BacktestAccount("test_1")
        self.account.bindStrategy(MarketMakingStrategy)
        
        self.account.deposit(100000000) #给账户充值
        self.account.adjustLeverage(1)  #设置当前账户的杠杆倍数


        #dbfile = rootpath.join_relative_path("marketquote.db")
        #conn = sqlite3.connect(dbfile)
        #c = conn.cursor()        
        #cursor = c.execute("SELECT f_lastprice, f_markprice, f_timestamp from t_market order by id")
        #for row in cursor:
        #    lastprice = float(row[0])
        #    markprice = float(row[1])         
        #    dt = datetime.datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
        #    self.account.processQuote((markprice, lastprice, dt))
        #conn.close()


        df = pd.read_csv(rootpath.join_relative_path("marketquote.csv"))
        if not df.empty:
            for index, row in df.iterrows():
                self.account.processQuote((row['price'], row['price'], row['time']))

#===============================================================================
#===============================================================================

def main():
    """主程序入口"""
    market = BacktestBitMEXMarket()
    market.run()

if __name__ == '__main__':
    main()
