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
    持仓测试,参考:snapshot\open-close-process-1
    """
    def __init__(self, pm):
        super(TestStrategy, self).__init__(pm)

    def onInit(self):
        """初始化策略"""
        pass
    
    def onTick(self, tick):
        """收到行情TICK推送"""
        try:
            '''
            Sell	107	5567.0	1,922,041 XBt	0.0750%	1,441 XBt	Market	900	0	5567.0
            Sell	265	5567.0	4,760,195 XBt	0.0750%	3,570 XBt	Market	900	107	5567.0
            Sell	25	5567.5	449,025 XBt	0.0750%	336 XBt	        Market	900	372	5567.0
            Sell	200	5568.0	3,592,000 XBt	0.0750%	2,694 XBt	Market	900	397	5567.0
            Sell	79	5568.0	1,418,840 XBt	0.0750%	1,064 XBt	Market	900	597	5567.0
            Sell	25	5568.0	449,000 XBt	0.0750%	336 XBt  	Market	900	676	5567.0
            Sell	20	5568.0	359,200 XBt	0.0750%	269 XBt	        Market	900	701	5567.0
            Sell	29	5568.0	520,840 XBt	0.0750%	390 XBt	        Market	900	721	5567.0
            Sell	150	5568.0	2,694,000 XBt	0.0750%	2,020 XBt	Market	900	750	5567.0
            Sell	100	5568.0	1,796,000 XBt	0.0750%	1,347 XBt	Market	100	0	5568.0            
            '''
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
                self.pm.placeOrder(DIRECTION_BUY, 3000.0, 90000)
                self.pm.placeOrder(DIRECTION_BUY, 3000.0, 10000)

            '''
            Buy	125	5569.0	-2,244,625 XBt	0.0750%	 1,683 XBt	Market	125	0	5569.0	
            
            Buy	409	5569.0	-7,344,413 XBt	0.0750%	 5,508 XBt	Market	875	0	5569.0	
            Buy	42	5568.5	-754,236 XBt	0.0750%	 565 XBt	Market	875	409	5569.0	
            Buy	200	5568.5	-3,591,600 XBt	0.0750%	 2,693 XBt	Market	875	451	5569.0	
            Buy	101	5568.5	-1,813,758 XBt	0.0750%	 1,360 XBt	Market	875	651	5569.0	
            Buy	17	5568.5	-305,286 XBt	0.0750%	 228 XBt	Market	875	752	5569.0	
            Buy	46	5568.5	-826,068 XBt	0.0750%	 619 XBt        Market	875	769	5569.0	
            Buy	50	5568.5	-897,900 XBt	0.0750%	 673 XBt        Market	875	815	5569.0	
            Buy	10	5568.5	-179,580 XBt	0.0750%	 134 XBt	Market	875	865	5569.0	                
            '''
            if tick.lastFillPrice == 5568.5:     
                self.pm.placeOrder(DIRECTION_BUY, 5568.5, 10)
                self.pm.placeOrder(DIRECTION_BUY, 5568.5, 50)
                self.pm.placeOrder(DIRECTION_BUY, 5568.5, 46)
                self.pm.placeOrder(DIRECTION_BUY, 5568.5, 17)            
                self.pm.placeOrder(DIRECTION_BUY, 5568.5, 101)  
                self.pm.placeOrder(DIRECTION_BUY, 5568.5, 200)  
                self.pm.placeOrder(DIRECTION_BUY, 5568.5, 42)  
            
            if tick.lastFillPrice == 5569.0 and tick.lastMarkPrice == 5486.95:     
                self.pm.placeOrder(DIRECTION_BUY, 5569.0, 409)
                
            if tick.lastFillPrice == 5569.0 and tick.lastMarkPrice == 5487.00:     
                self.pm.placeOrder(DIRECTION_BUY, 5569.0, 125)                

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
        
        tupleQuote4 = (5487.24, 5568.5)
        self.account.processQuote(tupleQuote4)   
        
        tupleQuote5 = (5486.95, 5569.0)
        self.account.processQuote(tupleQuote5)
        
        tupleQuote6 = (5487.00, 5569.0)
        self.account.processQuote(tupleQuote6)

#===============================================================================
#===============================================================================

def main():
    """主程序入口"""
    market = BacktestBitMEXMarket()
    market.run()

if __name__ == '__main__':
    main()
