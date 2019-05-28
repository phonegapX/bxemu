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

from datetime import datetime

from bxemu.constant import *
from bxemu.bitmexaccount import BacktestAccount
from bxemu.strategy import StrategyTemplate


class TestStrategy(StrategyTemplate):
    """
    持仓测试,参考:snapshot\open-close-process-3
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
  
            if tick.lastFillPrice == 5566.00 and tick.lastMarkPrice == 5483.06:
                self.pm.placeOrder(DIRECTION_SELL, 5566.0, 80)

            if tick.lastFillPrice == 5566.00 and tick.lastMarkPrice == 5481.34:
                self.pm.placeOrder(DIRECTION_SELL, 5566.00, 20)

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

        tupleQuote1 = (5483.17, 5566.50, datetime.now())
        self.account.processQuote(tupleQuote1)

        tupleQuote2 = (5483.23, 5566.50, datetime.now())
        self.account.processQuote(tupleQuote2)

        tupleQuote3 = (5483.06, 5566.00, datetime.now())
        self.account.processQuote(tupleQuote3)        
        
        tupleQuote4 = (5481.34, 5566.00, datetime.now())
        self.account.processQuote(tupleQuote4)

#===============================================================================
#===============================================================================

def main():
    """主程序入口"""
    market = BacktestBitMEXMarket()
    market.run()

if __name__ == '__main__':
    main()
