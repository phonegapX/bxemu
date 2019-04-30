#-*- coding:utf-8 –*-
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from functools import wraps

import sys
try:
    reload         # Python 2
    reload(sys)
    sys.setdefaultencoding('utf8')
except NameError:  # Python 3
    from importlib import reload
    reload(sys)

import math
import sympy

from bxemu.constant import *


class Position(object):
    """
    持仓数据类
    """

    def __init__(self, pm):
        """Constructor""" 
        self.clean()
        self.pm = pm

    def clean(self):
        '''
        清空仓位
        '''
        self.__side = EMPTY_UNICODE         #持仓方向(多仓或空仓)
        self.__size = EMPTY_INT             #目前仓位数量
        self.__entryValue = EMPTY_FLOAT     #开仓价值(界面没有显示): 多个成交(价值)累加
        self.__value = EMPTY_FLOAT          #当前价值 (仓位现时的名义价值)
        self.__entryPrice = EMPTY_FLOAT     #开仓价格 (目前多/空仓的平均买入/卖出价)
        self.__markPrice = EMPTY_FLOAT      #标记价格 (此价格用于计算盈亏和保证金，并有可能与合约最新成交价格有偏差以避免市场操控，这不会影响结算)
        self.__liqPrice = EMPTY_FLOAT       #强平价格 (如果该合约的标记价格低于该价格<多仓>或高于该价格<空仓>，你将会被强制平仓)
        self.__entryMargin = EMPTY_FLOAT    #开仓保证金(界面没有显示)
        self.__margin = EMPTY_FLOAT         #当前保证金 (被仓位使用并锁定的保证金，如果你有在某个仓位启用逐仓，此数值将会随着保证金下跌而减少，亦代表你的实际杠杆上升)
        self.__unrealisedPNL = EMPTY_FLOAT  #未实现盈亏
        self.__realisedPNL = EMPTY_FLOAT    #已实现盈亏 (自开仓以来的已实现盈亏)        
        self.__reviseOfMargin = EMPTY_FLOAT

    def holding(fn):
        '''
        装饰器函数,当前是否持有仓位
        '''
        @wraps(fn)
        def wrap(self, *args, **kwargs):
            if not self.isHolding():
                raise Exception("当前没有持仓")
            return fn(self, *args, **kwargs)
        return wrap

    def isHolding(self):
        '''
        当前是否持有仓位
        '''
        if self.side == EMPTY_UNICODE or self.size == EMPTY_INT or self.entryValue == EMPTY_FLOAT or self.entryPrice == EMPTY_FLOAT:
            return False
        else:
            return True

    def bankruptcyCheck(fn):
        '''
        装饰器函数,检查仓位是否破产
        '''
        @wraps(fn)
        def wrap(self, *args, **kwargs):
            result = None
            try:
                result = fn(self, *args, **kwargs)
                #如果仓位破产了就进行破产清算程序
                if self.isBankruptcy():
                    self.liquidate()
            except Exception as e:
                self.liquidate()
            return result
        return wrap

    def isBankruptcy(self):
        '''
        检查当前仓位是否被强平
        '''
        result = False
        try:
            if not self.isHolding():
                return result
            if self.pm.leverageType == 0:  #全仓模式
                xMargin = self.margin + self.pm.wallet.availableBalance - self.entryValue*TAKER_FEE_RATE/100  #用于计算强平价格
            else:   #逐仓模式
                xMargin = self.entryValue/self.pm.leverageType+self.entryValue*TAKER_FEE_RATE+self.unrealisedPNL   #用于计算强平价格，注意这里的计算方式有点不同
            #如果小于维持保证金就破产了
            if xMargin <= self.maintMargin:
                result = True
        except Exception as e:
            result = True
        return result

    @holding
    def liquidate(self):
        if self.pm.leverageType == 0:  #全仓模式,先取消此仓位的所有委托单,释放保证金,再检查保证金是否足够,如果仍然不足就破产
            self.pm.cancelAllOfOrders() #释放所有委托单
            self.reviseMargin()
            if self.isBankruptcy():     #再次检查是否破产
                self.pm.wallet.clean()  #钱包归0
                self.clean()            #仓位归0
        else:   #逐仓模式
            self.pm.wallet.walletBalance -= self.entryMargin    #损失开仓保证金
            self.clean()    #仓位归0
            self.pm.cancelAllOfOrders() #释放所有委托单,释放委托保证金
            self.pm.wallet.unrealisedPNL = EMPTY_FLOAT
            self.pm.wallet.positionMargin = EMPTY_FLOAT

    @holding
    @bankruptcyCheck
    def quotePrice(self, markPrice):
        self.markPrice = markPrice    #更新最新的标记价格
        #
        self.pm.wallet.unrealisedPNL = self.unrealisedPNL   #更新钱包余额,只模拟一个合约的情形
        self.pm.wallet.positionMargin = self.margin         #更新钱包余额,只模拟一个合约的情形
        #
        self.reviseMargin()
    #===================================================
    #持仓方向
    #===================================================
    @property
    def side(self):
        return self.__side
    
    @side.setter
    def side(self, value):
        if value != DIRECTION_SELL and value != DIRECTION_BUY:
            raise Exception("持仓方向不正确")
        self.__side = value

    #===================================================
    #目前仓位数量
    #===================================================
    @property
    def size(self):
        return self.__size
    
    @size.setter
    def size(self, value):
        if value < 0:
            raise Exception("仓位数量不能为负数") #不能为负数,这里的表达方式和bitmex不同
        self.__size = value

    #===================================================
    #开仓价值
    #===================================================
    @property
    def entryValue(self):
        return self.__entryValue
    
    @entryValue.setter
    def entryValue(self, value):
        if value < 0:
            raise Exception("开仓价值不能为负数") #不能为负数,这里的表达方式和bitmex不同
        self.__entryValue = value

    #===================================================
    #开仓价格
    #===================================================
    @property
    def entryPrice(self):
        return self.__entryPrice
    
    @entryPrice.setter
    def entryPrice(self, value):
        if value <= 0:
            raise Exception("开仓价格必须大于0") #必须大于0
        self.__entryPrice = value

    #===================================================
    #最低维持保证金,低于此保证金的话仓位将被强平
    #===================================================
    @property
    @holding
    def maintMargin(self):
        if self.pm.leverageType == 1 and self.side == DIRECTION_SELL:   #空仓一倍杠杆的情况下,维持保证金按0算.不要问我为什么bitmex就这样算的
            return 0
        else:
            return self.entryValue*(MAINTENANCE_RATE+TAKER_FEE_RATE+self.fundingRate)   #维持保证金=0.50% + 平仓佣金 + 资金费率

    #===================================================
    #当前价值
    #===================================================
    @property
    @holding
    def value(self):
        #价值(当前): 100000000/标记价格,结果四乘五入,再乘以仓位数量
        self.__value = round(100000000/self.markPrice)*self.size
        return self.__value

    #===================================================
    #强平价格
    #===================================================
    @property
    @holding
    def liqPrice(self):
        if self.pm.leverageType == 0:  #全仓模式
            xMargin = self.margin + self.pm.wallet.availableBalance - self.entryValue*TAKER_FEE_RATE/100  #用于计算强平价格
        else:   #逐仓模式
            xMargin = self.entryValue/self.pm.leverageType+self.entryValue*TAKER_FEE_RATE+self.unrealisedPNL   #用于计算强平价格，注意这里的计算方式有点不同                    
        #
        #强平价格: (100000000/标记价格-100000000/破产价格) * 仓位数量 = -(当前保证金-维持保证金) 维持保证金: 0.50%+平仓佣金+资金费率
        x = sympy.Symbol('x')
        # 解方程:
        if self.side == DIRECTION_BUY:
            f = self.value-100000000/x*self.size+(xMargin-self.maintMargin)
        elif self.side == DIRECTION_SELL:
            if self.pm.leverageType == 1:
                f = 100000000/x*self.size-self.value+(xMargin)  #不要问我为什么,bitmex就这样算的
            else:
                f = 100000000/x*self.size-self.value+(xMargin-self.maintMargin)
        r = sympy.solve(f, x)
        #
        self.__liqPrice = r[0]
        if self.__liqPrice <= 0:
            self.__liqPrice = 100000000
        return self.__liqPrice
    
    #===================================================
    #开仓保证金
    #===================================================
    @property
    @holding
    def entryMargin(self):
        leverageType = self.pm.leverageType
        if leverageType == 0:
            leverageType = 100  #全仓模式下保证金按100倍杠杆算
        if self.side == DIRECTION_SELL and leverageType == 1:
            self.__entryMargin = self.entryValue  #如果是空仓一倍杠杆那保证金就等于当前价值,不要问我为什么bitmex就是这样算的
        else:
            #开仓保证金 (开仓价值+开仓手续费)/杠杆倍数+平仓手续费(开仓价值*平仓手续费率)
            self.__entryMargin = (self.entryValue+self.entryValue*TAKER_FEE_RATE)/leverageType+self.entryValue*TAKER_FEE_RATE
            self.__entryMargin = math.ceil(self.__entryMargin)
        return self.__entryMargin

    #===================================================
    #当前保证金
    #===================================================
    @property
    @holding
    def margin(self):
        if self.pm.leverageType == 0:  #全仓模式
            if self.unrealisedPNL > 0:
                self.__margin = self.entryMargin+self.unrealisedPNL
            else:   #全仓模式下,如果是浮亏状态，当前保证金不会减少
                self.__margin = self.entryMargin + self.__reviseOfMargin
        else:   #逐仓模式
            #当前保证金: 开仓保证金 + 未实现盈亏
            self.__margin = self.entryMargin+self.unrealisedPNL
        if self.__margin < 0:
            raise Exception("当前保证金不能为负数")
        return self.__margin
    
    def reviseMargin(self):
        if self.pm.leverageType == 0:  #全仓模式
            if self.pm.wallet.availableBalance < 0:
                self.__reviseOfMargin = self.pm.wallet.availableBalance
            else:
                self.__reviseOfMargin = 0
            self.pm.wallet.positionMargin = self.margin

    def resetSomething(self):
        self.__reviseOfMargin = EMPTY_FLOAT

    #===================================================
    #未实现盈亏
    #===================================================
    @property
    @holding
    def unrealisedPNL(self):
        #未实现盈亏: 开仓价值-价值(当前),多仓和空仓方向是反的
        if self.side == DIRECTION_BUY:
            self.__unrealisedPNL = self.entryValue - self.value
        elif self.side == DIRECTION_SELL:
            self.__unrealisedPNL = self.value - self.entryValue
        return self.__unrealisedPNL

    #===================================================
    #已实现盈亏
    #===================================================
    @property
    @holding
    def realisedPNL(self):
        return self.__realisedPNL
    
    @realisedPNL.setter
    @holding
    def realisedPNL(self, value):
        self.__realisedPNL = value

    #===================================================
    #标记价格
    #===================================================
    @property
    @holding
    def markPrice(self):
        return self.__markPrice
    
    @markPrice.setter
    @holding
    def markPrice(self, value):
        if value <= 0:
            raise Exception("标记价格必须大于0")
        if value > 100000:
            raise Exception("标记价格不能大于100000")   #人为做个限制
        self.__markPrice = value

    #===================================================
    #当前的资金费率,用于计算维持保证金
    #===================================================
    def calcFR(self, side):
        if side == DIRECTION_BUY and FUNDING_RATE > 0:
            return FUNDING_RATE
        elif side == DIRECTION_SELL and FUNDING_RATE < 0:
            return abs(FUNDING_RATE)
        return 0.0

    @property
    @holding
    def fundingRate(self):
        return self.calcFR(self.side)

    def _longOpen(self, trade): 
        '''
        开多仓
        '''
        #持仓方向
        self.side = trade.side
        #目前仓位数量
        self.size = trade.execQty
        #开仓价值(界面没有显示)
        self.entryValue = trade.value
        #开仓均价: 开仓价值/仓位数量,结果四乘五入,假设舍入后的结果为A,然后再100000000/A (开仓或者加仓需要计算,减仓的情况下不计算维持之前不变)
        self.entryPrice = trade.execPrice
        #标记价格
        self.markPrice = self.pm.lastMarkPrice
        #已实现盈亏:多个成交的手续费累加,外加每八小时的费率交换,外加减仓的收益
        self.realisedPNL = -trade.feePaid
        #更新钱包余额
        self.pm.wallet.walletBalance += -trade.feePaid
        self.pm.wallet.unrealisedPNL = self.unrealisedPNL   #更新钱包余额,只模拟一个合约的情形
        self.pm.wallet.positionMargin = self.margin         #更新钱包余额,只模拟一个合约的情形

    def _longIncrease(self, trade): 
        '''
        持有多仓的情况下加仓
        '''
        #目前仓位数量
        self.size += trade.execQty
        #开仓价值(界面没有显示)
        self.entryValue += trade.value
        #开仓均价: 开仓价值/仓位数量,结果四乘五入,假设舍入后的结果为A,然后再100000000/A (开仓或者加仓需要计算,减仓的情况下不计算维持之前不变)
        self.entryPrice = 100000000/round(self.entryValue/self.size)
        #标记价格
        self.markPrice = self.pm.lastMarkPrice
        #已实现盈亏:多个成交的手续费累加,外加每八小时的费率交换,外加减仓的收益
        self.realisedPNL += -trade.feePaid
        #更新钱包余额
        self.pm.wallet.walletBalance += -trade.feePaid
        self.pm.wallet.unrealisedPNL = self.unrealisedPNL   #更新钱包余额,只模拟一个合约的情形
        self.pm.wallet.positionMargin = self.margin         #更新钱包余额,只模拟一个合约的情形

    def _longReduction(self, trade): 
        '''
        持有多仓的情况下减仓
        '''
        #目前仓位数量
        if trade.execQty < self.size:       #部分平仓
            x = round(self.entryValue/self.size)*trade.execQty
            self.size -= trade.execQty
            #开仓价值(界面没有显示)
            self.entryValue -= x
            #标记价格
            self.markPrice = self.pm.lastMarkPrice
            #已实现盈亏:多个成交的手续费累加,外加每八小时的费率交换,外加减仓的收益
            self.realisedPNL += -trade.feePaid
            self.realisedPNL += (x - trade.value)
            #更新钱包余额
            self.pm.wallet.walletBalance += -trade.feePaid
            self.pm.wallet.walletBalance += (x - trade.value)
            self.pm.wallet.unrealisedPNL = self.unrealisedPNL   #更新钱包余额,只模拟一个合约的情形
            self.pm.wallet.positionMargin = self.margin         #更新钱包余额,只模拟一个合约的情形
        elif trade.execQty == self.size:    #全部平仓
            #更新钱包余额
            self.pm.wallet.walletBalance += -trade.feePaid
            self.pm.wallet.walletBalance += (self.entryValue - trade.value)
            self.pm.wallet.unrealisedPNL = EMPTY_FLOAT  #更新钱包余额,只模拟一个合约的情形
            self.pm.wallet.positionMargin = EMPTY_FLOAT #更新钱包余额,只模拟一个合约的情形
            self.clean()    #仓位归0            
        else:   #由多变空
            t1, t2 = trade.split(self.size) #分割成二个成交
            #用第一个成交将当前仓位先全部平仓
            self.realisedPNL += -t1.feePaid
            self.realisedPNL += (self.entryValue - t1.value)
            self.pm.wallet.walletBalance += -t1.feePaid
            self.pm.wallet.walletBalance += (self.entryValue - t1.value)
            self.pm.wallet.unrealisedPNL = EMPTY_FLOAT  #更新钱包余额,只模拟一个合约的情形
            self.pm.wallet.positionMargin = EMPTY_FLOAT #更新钱包余额,只模拟一个合约的情形
            tmp = self.realisedPNL
            self.clean()    #仓位归0
            self._shortOpen(t2)  #用第二个成交重新开空仓
            self.realisedPNL += tmp

    def _shortOpen(self, trade): 
        '''
        开空仓
        '''
        self._longOpen(trade) #代码相同
    
    def _shortIncrease(self, trade):
        '''
        持有空仓的情况下加仓
        '''
        self._longIncrease(trade)   #代码相同
    
    def _shortReduction(self, trade): 
        '''
        持有空仓的情况下减仓
        '''
        #目前仓位数量
        if trade.execQty < self.size:       #部分平仓
            x = round(self.entryValue/self.size)*trade.execQty
            self.size -= trade.execQty
            #开仓价值(界面没有显示)
            self.entryValue -= x
            #标记价格
            self.markPrice = self.pm.lastMarkPrice
            #已实现盈亏:多个成交的手续费累加,外加每八小时的费率交换,外加减仓的收益
            self.realisedPNL += -trade.feePaid
            self.realisedPNL += (trade.value - x)
            #更新钱包余额
            self.pm.wallet.walletBalance += -trade.feePaid
            self.pm.wallet.walletBalance += (trade.value - x)
            self.pm.wallet.unrealisedPNL = self.unrealisedPNL   #更新钱包余额,只模拟一个合约的情形
            self.pm.wallet.positionMargin = self.margin         #更新钱包余额,只模拟一个合约的情形
        elif trade.execQty == self.size:    #全部平仓
            #更新钱包余额
            self.pm.wallet.walletBalance += -trade.feePaid
            self.pm.wallet.walletBalance += (trade.value - self.entryValue)
            self.pm.wallet.unrealisedPNL = EMPTY_FLOAT  #更新钱包余额,只模拟一个合约的情形
            self.pm.wallet.positionMargin = EMPTY_FLOAT #更新钱包余额,只模拟一个合约的情形
            self.clean()    #仓位归0
        else:   #由空变多
            t1, t2 = trade.split(self.size) #分割成二个成交
            #用第一个成交将当前仓位先全部平仓
            self.realisedPNL += -t1.feePaid
            self.realisedPNL += (t1.value - self.entryValue)
            self.pm.wallet.walletBalance += -t1.feePaid
            self.pm.wallet.walletBalance += (t1.value - self.entryValue)
            self.pm.wallet.unrealisedPNL = EMPTY_FLOAT  #更新钱包余额,只模拟一个合约的情形
            self.pm.wallet.positionMargin = EMPTY_FLOAT #更新钱包余额,只模拟一个合约的情形
            tmp = self.realisedPNL
            self.clean()    #仓位归0
            self._longOpen(t2)  #用第二个成交重新开多仓
            self.realisedPNL += tmp

    @bankruptcyCheck    
    def feeding(self, trade):
        if trade.side == DIRECTION_BUY: #买单成交
            if self.size == 0:     #当前没有持仓,开多仓
                self._longOpen(trade)
            elif self.size > 0 and self.side == DIRECTION_BUY:    #当前持有多仓,进行加仓
                self._longIncrease(trade)
            elif self.size > 0 and self.side == DIRECTION_SELL:   #当前持有空仓,进行减仓
                self._shortReduction(trade)
        elif trade.side == DIRECTION_SELL:  #卖单成交
            if self.size == 0:     #当前没有持仓,开空仓
                self._shortOpen(trade)
            elif self.size > 0 and self.side == DIRECTION_BUY:    #当前持有多仓,进行减仓
                self._longReduction(trade)
            elif self.size > 0 and self.side == DIRECTION_SELL:   #当前持有空仓,进行加仓
                self._shortIncrease(trade)
        #=================================================================================
        self.pm.notifyOrderChange(trade.orderId)            #委托单变化通知,主要目的是计算委托单保证金
        #
        self.reviseMargin()
        #
        #所有数据都已经准备完毕,这个时候可以计算仓位是否破产(破产检查代码放到了装饰器函数里面)