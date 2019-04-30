#-*- coding:utf-8 –*-

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

from bxemu.constant import *
from bxemu.bitmexaccount import BacktestAccount
from bxemu.strategy import StrategyTemplate


class TestStrategy(StrategyTemplate):
    """
    破产测试
    """
    def __init__(self, pm):
        super(TestStrategy, self).__init__(pm)

    def onInit(self):
        """初始化策略"""
        pass
    
    def onTick(self, tick):
        """收到行情TICK推送"""
        try:
            if tick.lastFillPrice == 5568.0:
                self.pm.placeOrder(DIRECTION_SELL, 5568.0, 100)
                self.pm.placeOrder(DIRECTION_SELL, 5568.0, 150)
                self.pm.placeOrder(DIRECTION_SELL, 5568.0, 29)
                self.pm.placeOrder(DIRECTION_SELL, 5568.0, 20)
                self.pm.placeOrder(DIRECTION_SELL, 5568.0, 25)
                self.pm.placeOrder(DIRECTION_SELL, 5568.0, 79)
                self.pm.placeOrder(DIRECTION_SELL, 5568.0, 200)
            if tick.lastFillPrice == 5567.5:
                self.pm.placeOrder(DIRECTION_SELL, 5567.5, 25)
            if tick.lastFillPrice == 5567.0:     
                self.pm.placeOrder(DIRECTION_SELL, 5567.0, 265)
                self.pm.placeOrder(DIRECTION_SELL, 5567.0, 107)
                #
                self.pm.placeOrder(DIRECTION_BUY, 3000.0, 50000)
                self.pm.placeOrder(DIRECTION_BUY, 3000.0, 100000)
                self.pm.placeOrder(DIRECTION_BUY, 3000.0, 50000)
                self.pm.placeOrder(DIRECTION_BUY, 3000.0, 80000)
                self.pm.placeOrder(DIRECTION_BUY, 3000.0, 10000)
        except Exception as e:
            print(e)

    def onOrder(self, order):
        """收到委托变化推送"""
        pass

    def onTrade(self, trade):
        """收到成交推送"""
        pass


class BacktestBitMEXMarket(object):
    
    def __init__(self):
        pass
    
    def run(self):  
        self.account = BacktestAccount()
        self.account.bindStrategy(TestStrategy)
        
        self.account.deposit(112753569) #给账户充值
        self.account.adjustLeverage(0)  #

        tupleQuote1 = (5487.24, 5568.00)
        self.account.processQuote(tupleQuote1)  
        
        tupleQuote2 = (5487.24, 5567.50)
        self.account.processQuote(tupleQuote2)
        
        tupleQuote3 = (5487.24, 5567.00)
        self.account.processQuote(tupleQuote3)
        
        tupleQuote4 = (5700.24, 5700.5)
        self.account.processQuote(tupleQuote4)   
        
        tupleQuote5 = (5900.95, 5900.0)
        self.account.processQuote(tupleQuote5)
        
        tupleQuote6 = (6100.39, 6100.0)
        self.account.processQuote(tupleQuote6)
        
        tupleQuote7 = (6147.00, 6147.0)
        self.account.processQuote(tupleQuote7)
        
        tupleQuote8 = (6180.55, 6180.55)
        self.account.processQuote(tupleQuote8)
        
        tupleQuote9 = (6182.05, 6182.0)
        self.account.processQuote(tupleQuote9)
#===============================================================================
#===============================================================================

def main():
    """主程序入口"""
    market = BacktestBitMEXMarket()
    market.run()

if __name__ == '__main__':
    main()
