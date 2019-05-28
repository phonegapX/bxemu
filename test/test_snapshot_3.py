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
    委托保证金计算测试,参考:snapshot\3.png
    """
    def __init__(self, pm):
        super(TestStrategy, self).__init__(pm)

    def onInit(self):
        """初始化策略"""
        pass
    
    def onTick(self, tick):
        """收到行情TICK推送"""
        try:
            self.pm.placeOrder(DIRECTION_SELL, 5535.5, 100)
            #
            self.pm.placeOrder(DIRECTION_SELL, 6776.0, 150)
            self.pm.placeOrder(DIRECTION_BUY, 3776.0, 130)
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
        
        self.account.deposit(112796528) #给账户充值
        self.account.adjustLeverage(1)  #

        tupleQuote1 = (5483.96, 5535.50, datetime.now())
        self.account.processQuote(tupleQuote1)
        

#===============================================================================
#===============================================================================

def main():
    """主程序入口"""
    market = BacktestBitMEXMarket()
    market.run()

if __name__ == '__main__':
    main()
