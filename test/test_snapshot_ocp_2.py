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
    持仓测试,参考:snapshot\open-close-process-2
    """
    def __init__(self, pm):
        super(TestStrategy, self).__init__(pm)

    def onInit(self):
        """初始化策略"""
        pass
    
    def onTick(self, tick):
        """收到行情TICK推送"""
        try:
            if tick.lastFillPrice == 5568.00 and tick.lastMarkPrice == 5484.27:
                self.pm.placeOrder(DIRECTION_SELL, 5568.0, 60)
                self.pm.placeOrder(DIRECTION_BUY, 3487.0, 5000)
            
            if tick.lastFillPrice == 5568.00 and tick.lastMarkPrice == 5482.54:
                self.pm.placeOrder(DIRECTION_SELL, 5568.0, 40)
  
            if tick.lastFillPrice == 5568.50 and tick.lastMarkPrice == 5485.45:
                self.pm.placeOrder(DIRECTION_BUY, 5568.5, 80)

            if tick.lastFillPrice == 5568.50 and tick.lastMarkPrice == 5485.11:
                self.pm.placeOrder(DIRECTION_BUY, 5568.5, 20)                

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
        
        self.account.deposit(112756461) #给账户充值
        self.account.adjustLeverage(0)  #

        tupleQuote1 = (5484.27, 5568.00)
        self.account.processQuote(tupleQuote1)

        tupleQuote2 = (5482.54, 5568.00)
        self.account.processQuote(tupleQuote2)

        tupleQuote3 = (5485.45, 5568.50)
        self.account.processQuote(tupleQuote3)        
        
        tupleQuote4 = (5485.11, 5568.50)
        self.account.processQuote(tupleQuote4)         

#===============================================================================
#===============================================================================

def main():
    """主程序入口"""
    market = BacktestBitMEXMarket()
    market.run()

if __name__ == '__main__':
    main()
