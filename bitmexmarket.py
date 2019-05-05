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
import bxemu.util as util
import rootpath


class MarketMakingStrategy(StrategyTemplate):
    """
    简单做市商策略
    """
    
    once = 1
    
    def __init__(self, pm):
        super(MarketMakingStrategy, self).__init__(pm)

    def onInit(self):
        """初始化策略"""
        pass
    
    def onTick(self, tick):
        """收到行情TICK推送"""
        
        try:
            if MarketMakingStrategy.once == 1:

                self.pm.placeOrder(DIRECTION_SELL, 7000, 100)
                
                self.pm.placeOrder(DIRECTION_SELL, 8000, 170)
                
                self.pm.placeOrder(DIRECTION_SELL, 9000, 66)
                
                self.pm.placeOrder(DIRECTION_SELL, 3000, 100)
                
                MarketMakingStrategy.once+=1
                
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
        
        self.account = BacktestAccount()
        self.account.bindStrategy(MarketMakingStrategy)
        
        self.account.deposit(100000000) #给账户充值
        self.account.adjustLeverage(1)  #设置当前账户的杠杆倍数

        listQuote = util.load_pickle(rootpath.join_relative_path("simple_quote.list"))

        for x in listQuote:
            self.account.processQuote((x, x))

#===============================================================================
#===============================================================================

def main():
    """主程序入口"""
    market = BacktestBitMEXMarket()
    market.run()

if __name__ == '__main__':
    main()
