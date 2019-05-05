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
bxemu.constant.FUNDING_RATE = 0.000885
"""

class TestStrategy(StrategyTemplate):
    """
    多仓转空仓,参考:snapshot\long-to-short
    """
    def __init__(self, pm):
        super(TestStrategy, self).__init__(pm)

    def onInit(self):
        """初始化策略"""
        pass
    
    def onTick(self, tick):
        """收到行情TICK推送"""
        try:
            if tick.lastFillPrice == 5140.00:
                self.pm.placeOrder(DIRECTION_BUY, 5140.00, 200)
            
            if tick.lastFillPrice == 5139.50:
                self.pm.placeOrder(DIRECTION_SELL, 5139.50, 277)
  
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
        
        self.account.deposit(112714889) #给账户充值
        self.account.adjustLeverage(3)  #

        tupleQuote1 = (5158.95, 5140.00)
        self.account.processQuote(tupleQuote1)

        tupleQuote2 = (5158.70, 5139.50)
        self.account.processQuote(tupleQuote2)


#===============================================================================
#===============================================================================

def main():
    """主程序入口"""
    market = BacktestBitMEXMarket()
    market.run()

if __name__ == '__main__':
    main()
