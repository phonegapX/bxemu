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
            if tick.lastFillPrice == 5566.50 and tick.lastMarkPrice == 5483.17:
                self.pm.placeOrder(DIRECTION_BUY, 5566.50, 70)
            
            if tick.lastFillPrice == 5566.50 and tick.lastMarkPrice == 5483.23:
                self.pm.placeOrder(DIRECTION_BUY, 5566.50, 30)
                #
                self.pm.placeOrder(DIRECTION_BUY, 3000.50, 1000)
                self.pm.placeOrder(DIRECTION_BUY, 3500.50, 870)
                self.pm.placeOrder(DIRECTION_SELL, 7566.50, 630)
                self.pm.placeOrder(DIRECTION_SELL, 8566.50, 1930)

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
        self.account = BacktestAccount("test")
        self.account.bindStrategy(TestStrategy)
        
        self.account.deposit(112763781) #给账户充值
        self.account.adjustLeverage(10)  #

        tupleQuote1 = (5483.17, 5566.50)
        self.account.processQuote(tupleQuote1)

        tupleQuote2 = (5483.23, 5566.50)
        self.account.processQuote(tupleQuote2)

        tupleQuote3 = (5300.06, 5566.00)
        self.account.processQuote(tupleQuote3)        
        
        tupleQuote4 = (5200.34, 5200.00)
        self.account.processQuote(tupleQuote4)
        
        tupleQuote5 = (5100.34, 5100.00)
        self.account.processQuote(tupleQuote5)
        
        tupleQuote6 = (5089.71, 5089.00)
        self.account.processQuote(tupleQuote6)
        
        tupleQuote7 = (5089.70, 5089.00)
        self.account.processQuote(tupleQuote7)

#===============================================================================
#===============================================================================

def main():
    """主程序入口"""
    market = BacktestBitMEXMarket()
    market.run()

if __name__ == '__main__':
    main()
