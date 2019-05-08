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

"""
需要修改:
bxemu.constant.FUNDING_RATE = 0.001071
"""

class TestStrategy(StrategyTemplate):
    """
    空仓转多仓,参考:snapshot\short-to-long
    """
    def __init__(self, pm):
        super(TestStrategy, self).__init__(pm)

    def onInit(self):
        """初始化策略"""
        pass
    
    def onTick(self, tick):
        """收到行情TICK推送"""
        try:
            if tick.lastFillPrice == 5173.00:
                self.pm.placeOrder(DIRECTION_SELL, 5173.00, 100)
            
            if tick.lastFillPrice == 5164.50:
                self.pm.placeOrder(DIRECTION_SELL, 5164.50, 100)
  
            if tick.lastFillPrice == 5165.00:
                self.pm.placeOrder(DIRECTION_BUY, 5165.00, 267)

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
        
        self.account.deposit(112704993) #给账户充值
        self.account.adjustLeverage(0)  #

        tupleQuote1 = (5151.72, 5173.00)
        self.account.processQuote(tupleQuote1)

        tupleQuote2 = (5151.72, 5164.50)
        self.account.processQuote(tupleQuote2)

        tupleQuote3 = (5151.70, 5165.00)
        self.account.processQuote(tupleQuote3)        
        

#===============================================================================
#===============================================================================

def main():
    """主程序入口"""
    market = BacktestBitMEXMarket()
    market.run()

if __name__ == '__main__':
    main()
