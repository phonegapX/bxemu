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

import os
import math
import random
import copy

from .statistic import Statistic
from .position import Position
from .wallet import Wallet
from bxemu.constant import *
from bxemu.util.sequence import SequenceGenerator


def XBt_to_XBT(XBt):
    return float(XBt) / XBt_TO_XBT

class PortfolioManager(object):
    """
    投资管理
    """
    
    def __init__(self, name):
        self.name = name                #账户名,用于区分多个账户
        self.orderBook = []             #订单簿
        self.trades = []                #成交列表
        self.position = Position(self)  #持仓信息
        self.wallet = Wallet()          #钱包信息
        self.leverageType = EMPTY_INT   #杠杆类型(0到100),0代表全仓模式
        self.lastMarkPrice = EMPTY_FLOAT   #最新合理标记价格
        self.lastFillPrice = EMPTY_FLOAT   #最新期货成交价格
        self.lastQuoteTime = None       #最后报价时间
        self.sg = SequenceGenerator()
        self.stat = Statistic()

    def placeOrder(self, side, price, size):
        raise Exception("需要子类继承,并且实现此函数")

    def cancelOrder(self, orderId):
        raise Exception("需要子类继承,并且实现此函数")

    def cancelAllOfOrders(self):
        raise Exception("需要子类继承,并且实现此函数")

    def _allowTrade(self, order, tradeVol, fillPrice, markPrice, tradeType):
        """
        判断是否允许成交(比如说一成交就会导致仓位爆仓的情况就不允许成交)
        """
        wallet = copy.deepcopy(self.wallet) #复制钱包,目的是不会影响真正的钱包
        tradeValue = round(100000000/fillPrice)*tradeVol    #成交价值        
        if tradeType == TRADE_TYPE_MAKER:
            feePaid = math.floor(MAKER_FEE_RATE*tradeValue)   #已付费用
        else:
            feePaid = math.floor(TAKER_FEE_RATE*tradeValue)   #已付费用
        #
        if not self.position.isHolding() : #开仓的情形
            #目前仓位数量
            positionSize = tradeVol
            #开仓价值(界面没有显示)
            entryValue = tradeValue
            #已实现盈亏:多个成交的手续费累加,外加每八小时的费率交换,外加减仓的收益
            #realisedPNL = -feePaid
            #更新钱包余额
            wallet.walletBalance += -feePaid
        elif self.position.isHolding() and (\
            (self.position.side == DIRECTION_BUY and order.side == DIRECTION_BUY) or \
            (self.position.side == DIRECTION_SELL and order.side == DIRECTION_SELL)):    #加仓的情形
            #目前仓位数量
            positionSize = self.position.size + tradeVol
            #开仓价值(界面没有显示)
            entryValue = self.position.entryValue + tradeValue
            #已实现盈亏:多个成交的手续费累加,外加每八小时的费率交换,外加减仓的收益
            #realisedPNL = self.position.realisedPNL + -feePaid
            #更新钱包余额
            wallet.walletBalance += -feePaid
        else:
            return True #减仓的情况下,不需要判断是否会爆仓的问题,直接允许

        #价值(当前): 100000000/标记价格,结果四乘五入,再乘以仓位数量
        value = round(100000000/markPrice)*positionSize
        
        #未实现盈亏: 开仓价值-价值(当前),多仓和空仓方向是反的
        if order.side == DIRECTION_BUY:
            unrealisedPNL = entryValue - value
        elif order.side == DIRECTION_SELL:
            unrealisedPNL = value - entryValue

        try:
            leverageType = self.leverageType
            if leverageType == 0:
                leverageType = 100  #全仓模式下保证金按100倍杠杆算
            if order.side == DIRECTION_SELL and leverageType == 1:
                entryMargin = entryValue  #如果是空仓一倍杠杆那保证金就等于当前价值,不要问我为什么bitmex就是这样算的
            else:
                #开仓保证金 (开仓价值+开仓手续费)/杠杆倍数+平仓手续费(开仓价值*平仓手续费率)
                entryMargin = (entryValue+entryValue*TAKER_FEE_RATE)/leverageType+entryValue*TAKER_FEE_RATE
                entryMargin = math.ceil(entryMargin)
            #=================================================================================
            if self.leverageType == 0:  #全仓模式
                if unrealisedPNL > 0:
                    margin = entryMargin+unrealisedPNL
                else:   #全仓模式下,如果是浮亏状态，当前保证金不会减少
                    margin = entryMargin
            else:   #逐仓模式
                #当前保证金: 开仓保证金 + 未实现盈亏
                margin = entryMargin+unrealisedPNL
            if margin < 0:
                raise Exception("当前保证金不能为负数")
            #=================================================================================
            wallet.unrealisedPNL = unrealisedPNL   #更新钱包余额,只模拟一个合约的情形
            wallet.positionMargin = margin         #更新钱包余额,只模拟一个合约的情形
            #
            order = copy.deepcopy(order)    #这样不会影响真正的订单对象
            order.left -= tradeVol
            if order.left == 0:
                if sys.version_info.major == 2:
                    l = filter(lambda o:o.orderId!=order.orderId, self.orderBook) #完全成交的委托单要去掉
                else:
                    l = list(filter(lambda o:o.orderId!=order.orderId, self.orderBook)) #完全成交的委托单要去掉
            else:
                l = self.orderBook
            wallet.orderMargin = self._calculateOrderMargin(l, positionSize, order.side)  #重新计算委托单保证金
            #============================================================================
            if self.leverageType == 1 and order.side == DIRECTION_SELL:   #空仓一倍杠杆的情况下,维持保证金按0算.不要问我为什么bitmex就这样算的
                maintMargin = 0
            else:
                maintMargin = entryValue*(MAINTENANCE_RATE+TAKER_FEE_RATE+self.position.calcFR(order.side))   #维持保证金=0.50% + 平仓佣金 + 资金费率
            #开始检查当前仓位是否被强平
            if self.leverageType == 0:  #全仓模式
                xMargin = margin + wallet.availableBalance - entryValue*TAKER_FEE_RATE/100  #用于计算强平价格
            else:   #逐仓模式
                xMargin = entryValue/self.leverageType+entryValue*TAKER_FEE_RATE+unrealisedPNL   #用于计算强平价格，注意这里的计算方式有点不同
            #如果小于维持保证金就破产了
            if xMargin <= maintMargin:
                return False
            return True
        except Exception as e:
            return False

    def _obtainTransactionVolume(self, maxVolume):
        """
        用于模拟本次交易实际成交的数量,参数maxVolume是最大可成交数量,返回值为实际成交的数量
        这里设置两个随机数,一个随机数用于模拟是否全部成交,另一个随机数用于模拟在部分成交的情况下实际成交的数量
        """
        assert maxVolume > 0
        assert TV_PERCENTAGE >= 0 and TV_PERCENTAGE <= 100
        isPartial = False
        if TV_PERCENTAGE == 100 or (TV_PERCENTAGE > 0 and random.randint(1, 100) > 100-TV_PERCENTAGE):  #有多少概率不能完全成交
            isPartial = True
        if isPartial:   #部分成交
            volume = random.randint(1, maxVolume)   #随机获取可以成交的数量
        else:           #全部成交
            volume = maxVolume
        return volume

    def adjustLeverage(self, type):
        """
        目前只支持整数倍杠杆,不超过100倍,也不支持动态调整杠杆
        """
        assert type - (int(type)) == 0
        assert type >= 0 and type <= 100        
        self.leverageType = type

    def bindStrategy(self, cls):
        self.strategy = cls(self)
        self.strategy.onInit()
        
        #hook策略的回调函数
        self._onOrder = self.strategy.onOrder
        self.strategy.onOrder = self._onOrderHook
        #
        self._onTrade = self.strategy.onTrade
        self.strategy.onTrade = self._onTradeHook
        #
        self._onTick = self.strategy.onTick
        self.strategy.onTick = self._onTickHook

    def deposit(self, xbt):
        assert xbt > 0  #充值数量必须大于0
        self.wallet.walletBalance += xbt
        #统计记录
        self.stat.log(Statistic.OP_WALLET_DEPOSIT, self, None)

    def _calculateOrderMargin(self, orderBook, positionSize, positionSide):
        """
        在bitmex中一个<交易对>持仓有三种可能：1没有持仓 2持有多仓 3持有空仓
        
        举个例子(没有持仓的情况):
        1.当前没有仓位。买多10张合约，卖空6张合约，10>6，只计算10张多单合约的委托保证金
        2.当前没有仓位。买多10张合约，卖空10张合约，10>=10，只计算10张多单合约的委托保证金
        3.当前没有仓位。买多10张合约，卖空13张合约，10<13，10张多单合约的委托保证金+3张(13-10)空单合约的委托保证金
        
        举个例子(持有多仓):
        1.持有多仓10张合约。买多15张合约，卖空6张合约，第一步先进行抵消操作，6张空单全部抵消完，只计算15张多单合约的委托保证金
        2.持有多仓10张合约。买多15张合约，卖空13张合约，第一步先进行抵消操作，13张空单抵消后还剩3张卖空合约，然后再按之前的计算规则15>3,只计算15张多单合约的委托保证金
        3.持有多仓10张合约。买多15张合约，卖空27张合约，第一步先进行抵消操作，27张空单抵消后还剩17(27-10)张卖空合约，然后再按之前的计算规则15<17, 结果=15张多单合约的委托保证金+2张(17-15)空单合约的委托保证金
        
        举个例子(持有空仓):
        1.持有空仓10张合约。卖空15张合约，买多6张合约，第一步先进行抵消操作，6张多单全部抵消完，只计算15张空单合约的委托保证金
        2.持有空仓10张合约。卖空15张合约，买多13张合约，第一步先进行抵消操作，13张多单抵消后还剩3张买多合约，然后再按之前的计算规则3<15,结果=3张多单合约的委托保证金+12张(15-3)空单合约的委托保证金
        3.持有空仓10张合约。卖空15张合约，买多27张合约，第一步先进行抵消操作，27张多单抵消后还剩17(27-10)张买多合约，然后再按之前的计算规则17>15, 只计算17张多单合约的委托保证金
        """
        
        longPosSize = 0     #所有多委单的仓位总和
        longPosValue = 0    #所有多委单的价值总和
        
        shortPosSize = 0    #所有空委单的仓位总和
        shortPosValue = 0   #所有空委单的价值总和
        
        #理解成: 多个多委单合并成一个多委单，多个空委单合并成一个空委单
        for order in orderBook:
            if order.side == DIRECTION_BUY:
                longPosSize += order.left
                longPosValue += order.value
            elif order.side == DIRECTION_SELL:
                shortPosSize += order.left
                shortPosValue += order.value

        leverageType = self.leverageType
        
        if leverageType == 0:
            leverageType = 100 #全仓模式下保证金按100倍杠杆算
        
        orderMargin = 0
        
        if positionSize == 0:     #当前没有持仓
            if longPosSize > 0:
                #委托保证金 = (委托价值+委托价值*开仓手续费率) / 杠杆倍数 + 开仓手续费(委托价值*开仓手续费率) + 平仓手续费(委托价值*平仓手续费率)
                orderMargin = (longPosValue+longPosValue*TAKER_FEE_RATE)/leverageType + longPosValue*TAKER_FEE_RATE + longPosValue*TAKER_FEE_RATE
            if shortPosSize > longPosSize:
                shortPosValue = shortPosValue/shortPosSize*(shortPosSize-longPosSize)
                m = (shortPosValue+shortPosValue*TAKER_FEE_RATE)/leverageType + shortPosValue*TAKER_FEE_RATE + shortPosValue*TAKER_FEE_RATE
                orderMargin += m
        elif positionSize > 0 and positionSide == DIRECTION_BUY:    #当前持有多仓
            #先进行抵消操作
            if shortPosSize > positionSize:
                s = shortPosSize - positionSize
            else:
                s = 0
            #计算委托保证金    
            if longPosSize > 0:
                #委托保证金 = (委托价值+委托价值*开仓手续费率) / 杠杆倍数 + 开仓手续费(委托价值*开仓手续费率) + 平仓手续费(委托价值*平仓手续费率)
                orderMargin = (longPosValue+longPosValue*TAKER_FEE_RATE)/leverageType + longPosValue*TAKER_FEE_RATE + longPosValue*TAKER_FEE_RATE
            if s > longPosSize:
                shortPosValue = shortPosValue/shortPosSize*(s-longPosSize)
                m = (shortPosValue+shortPosValue*TAKER_FEE_RATE)/leverageType + shortPosValue*TAKER_FEE_RATE + shortPosValue*TAKER_FEE_RATE
                orderMargin += m
        elif positionSize > 0 and positionSide == DIRECTION_SELL:    #当前持有空仓
            #先进行抵消操作
            if longPosSize > positionSize:
                l = longPosSize - positionSize
            else:
                l = 0
            if l > 0:
                #委托保证金 = (委托价值+委托价值*开仓手续费率) / 杠杆倍数 + 开仓手续费(委托价值*开仓手续费率) + 平仓手续费(委托价值*平仓手续费率)
                longPosValue = longPosValue/longPosSize*l
                orderMargin = (longPosValue+longPosValue*TAKER_FEE_RATE)/leverageType + longPosValue*TAKER_FEE_RATE + longPosValue*TAKER_FEE_RATE
            if shortPosSize > l:
                shortPosValue = shortPosValue/shortPosSize*(shortPosSize-l)
                m = (shortPosValue+shortPosValue*TAKER_FEE_RATE)/leverageType + shortPosValue*TAKER_FEE_RATE + shortPosValue*TAKER_FEE_RATE
                orderMargin += m  

        return math.ceil(orderMargin)

    def _onOrderHook(self, order):
        """
        收到委托变化推送
        有六种情况会产生onOrder回调:
        第一:完全成交
        第二:部分成交
        第三:用户主动取消
        第四:成交失败后取消(比如说一成交就会爆仓的情况)
        第五:爆仓后取消所有未完成订单
        第六:创建新订单
        备注:因为保证金不足而导致挂单失败的不算,因为这种情况订单都没有进入订单列表        
        """
        if order.left > 0 and order.size == order.left:  #新增委托单
            self.orderBook.append(order)    #将委托单添加进订单列表
            orderMargin = self._calculateOrderMargin(self.orderBook, self.position.size, self.position.side)   #计算委托保证金
            if orderMargin <= self.wallet.availableBalance+self.wallet.orderMargin:
                self.wallet.orderMargin = orderMargin  #只模拟一个合约的情形
            else:   #保证金不够,无法下单
                self.orderBook.remove(order)    #将订单移除
                raise Exception("可用余额不够,无法下单")  #抛出异常
        elif order.left > 0 and order.left < order.size:    #委托单部分成交(代码还没完全实现)
            self.wallet.orderMargin = self._calculateOrderMargin(self.orderBook, self.position.size, self.position.side)  #重新计算委托保证金
        else:   #此委托单已经完全成交,从列表删除
            self.orderBook.remove(order)
            self.wallet.orderMargin = self._calculateOrderMargin(self.orderBook, self.position.size, self.position.side)  #只模拟一个合约的情形

        self._onOrder(order)

    def _onTradeHook(self, trade):
        """
        收到成交推送
        """
        self.trades.append(trade)
        self.position.feeding(trade)
        self._onTrade(trade)

    def _onTickHook(self, tick):
        if self.position.isHolding():
            self.position.quotePrice(tick.lastMarkPrice)
        self._onTick(tick)
        #==============================
        self._outputStatus()
        #==============================
        self.position.resetSomething()

    def notifyOrderChange(self, orderId):
        """
        成交导致仓位变化,仓位变化后此函数会被调用,目的主要是计算委托保证金
        """
        if sys.version_info.major == 2:
            l = filter(lambda order:order.orderId==orderId, self.orderBook)
        else:
            l = list(filter(lambda order:order.orderId==orderId, self.orderBook))
        order = l[0]
        if order.left == 0:
            order.status = "Filled"
        else:
            order.status = "Partial filled"
        self.strategy.onOrder(order)

    def _outputStatus(self):
        #os.system('cls')
        #os.system('clear')
        print("====================================================================================================================")
        print("Account: %-8s  Currency: %-4s  Quote: USD  Leverage: %-3d  LastTradePrice: %-8.2f  LastMarkPrice: %-8.2f  Count: %-8d"%(self.name, PREFERENCES_CURRENCY, self.leverageType, self.lastFillPrice, self.lastMarkPrice, self.sg.get_next('count')))
        print("")
        print("%-13s  %-13s  %-13s  %-13s  %-13s  %-13s  %-13s  %-13s  %-13s"%("Size", "Side", "Value", "EntryPrice", "MarkPrice", "LiqPrice", "Margin", "UnrealisedPNL", "RealisedPNL"))
        if self.position.isHolding():
            if PREFERENCES_CURRENCY == CURRENCY_XBt:
                print("%-13d  %-13s  %-13.0f  %-13.2f  %-13.2f  %-13.2f  %-13.0f  %-13.0f  %-13.0f"%(self.position.size, self.position.side, self.position.value, self.position.entryPrice, self.position.markPrice, self.position.liqPrice, self.position.margin, self.position.unrealisedPNL, self.position.realisedPNL))
            else:
                print("%-13d  %-13s  %-13.6f  %-13.2f  %-13.2f  %-13.2f  %-13.6f  %-13.6f  %-13.6f"%(self.position.size, self.position.side, XBt_to_XBT(self.position.value), self.position.entryPrice, self.position.markPrice, self.position.liqPrice, XBt_to_XBT(self.position.margin), XBt_to_XBT(self.position.unrealisedPNL), XBt_to_XBT(self.position.realisedPNL)))
        print("")
        print("%-15s  %-15s  %-15s  %-15s  %-15s  %-15s"%("WalletBalance", "UnrealisedPNL", "MarginBalance", "PositionMargin", "OrderMargin", "AvailableBalance"))
        if PREFERENCES_CURRENCY == CURRENCY_XBt:
            print("%-15.0f  %-15.0f  %-15.0f  %-15.0f  %-15.0f  %-15.0f"%(self.wallet.walletBalance, self.wallet.unrealisedPNL, self.wallet.marginBalance, self.wallet.positionMargin, self.wallet.orderMargin, self.wallet.availableBalance))
        else:
            print("%-15.6f  %-15.6f  %-15.6f  %-15.6f  %-15.6f  %-15.6f"%(XBt_to_XBT(self.wallet.walletBalance), XBt_to_XBT(self.wallet.unrealisedPNL), XBt_to_XBT(self.wallet.marginBalance), XBt_to_XBT(self.wallet.positionMargin), XBt_to_XBT(self.wallet.orderMargin), XBt_to_XBT(self.wallet.availableBalance)))
        print("")
        print("%-12s  %-12s  %-12s  %-12s  %-12s  %-12s  %-12s  %-12s"%("OrderID", "Side", "Qty", "OrderPrice", "Remaining", "OrderValue", "Type", "Status"))
        for order in self.orderBook:
            if PREFERENCES_CURRENCY == CURRENCY_XBt:
                print("%-12d  %-12s  %-12d  %-12.2f  %-12d  %-12.0f  %-12s  %-12s"%(order.orderId, order.side, order.size, order.price, order.left, order.value, order.type, order.status))
            else:
                print("%-12d  %-12s  %-12d  %-12.2f  %-12d  %-12.6f  %-12s  %-12s"%(order.orderId, order.side, order.size, order.price, order.left, XBt_to_XBT(order.value), order.type, order.status))
        print("")
        print("Trade total: %d"%(len(self.trades)))
        print("====================================================================================================================")       

"""
开仓,加仓,减仓,平仓

开多仓:
第一笔是买单......最后一笔是卖单
开空仓:
第一笔是卖单......最后一笔是买单

每笔限价单:
1.先下委托单
2.委托单成交

==============================================================================
单笔委托单的委托保证金的计算公式(计算是以比特币(XBT)的最小单位聪(XBt)为单位):
1XBT=100000000XBt

委托价值=100000000/挂单价格*仓位数 (备注:100000000/挂单价格 这一步结果四舍五入成整数,然后再去乘以 仓位数)

委托保证金 = (委托价值+委托价值*开仓手续费率) / 杠杆倍数 + 开仓手续费(委托价值*开仓手续费率) + 平仓手续费(委托价值*平仓手续费率)
如果结果最后出现小数，去掉小数，不考虑四舍五入，结果直接加一，比如:
100000.2 => 100001

例子:买入开多,仓位100张合约, 挂单价格为2377.5，杠杆三倍
此单的委托价值为:100000000/2377.5*100
100000000/2377.5 = 42060.98843322818 = 42061
42061 * 100 = 4206100
委托价值=4206100聪 
代入公式：
委托保证金 = (4206100+4206100*0.00075) / 3 + 4206100*0.00075 + 4206100*0.00075
=1403084.858333333+3154.575+3154.575=1409394.008333333
=1409395

例子:买入开多,仓位997张合约, 挂单价格为997，杠杆三倍
此单的委托价值为:100000000/997*997
100000000/997 = 100300.9027081244 = 100301
100301 * 997 = 100000097
委托价值=100000097聪
代入公式：
委托保证金 = (100000097+100000097*0.00075) / 3 + 100000097*0.00075 + 100000097*0.00075
委托保证金 = (100000097+75000.07275) / 3 + 75000.07275 + 75000.07275
委托保证金 = 100075097.07275 / 3 + 75000.07275 + 75000.07275
委托保证金 = 33358365.69091667 + 75000.07275 + 75000.07275
委托保证金 = 33508365.83641667

如果同一个方向有多个挂单，可以理解为一笔挂单，这笔挂单的委托价值就是多个挂单委托价值的总和，实际不需要关注平均价格，如果需要平均价格也可以通过委托价值总和
推算出来，而不是用仓位总和进行推算。

委托保证金的计算规则是 减仓不需要保证金，那么第一步先把委托挂单抵消掉当前持仓，然后在计算，计算规则简单理解为：
1.委托多单仓位>=委托空单仓位,只计算多单的委托保证金
2.委托多单仓位<委托空单仓位,委托保证金=多单仓位的委托保证金+(委托空仓仓位-委托多仓仓位)的委托保证金

在bitmex中一个<交易对>持仓有三种可能：1没有持仓 2持有多仓 3持有空仓

举个例子(没有持仓的情况):
1.当前没有仓位。买多10张合约，卖空6张合约，10>6，只计算10张多单合约的委托保证金
2.当前没有仓位。买多10张合约，卖空10张合约，10>=10，只计算10张多单合约的委托保证金
3.当前没有仓位。买多10张合约，卖空13张合约，10<13，10张多单合约的委托保证金+3张(13-10)空单合约的委托保证金

举个例子(持有多仓):
1.持有多仓10张合约。买多15张合约，卖空6张合约，第一步先进行抵消操作，6张空单全部抵消完，只计算15张多单合约的委托保证金
2.持有多仓10张合约。买多15张合约，卖空13张合约，第一步先进行抵消操作，13张空单抵消后还剩3张卖空合约，然后再按之前的计算规则15>3,只计算15张多单合约的委托保证金
3.持有多仓10张合约。买多15张合约，卖空27张合约，第一步先进行抵消操作，27张空单抵消后还剩17(27-10)张卖空合约，然后再按之前的计算规则15<17, 结果=15张多单合约的委托保证金+2张(17-15)空单合约的委托保证金

举个例子(持有空仓):
1.持有空仓10张合约。卖空15张合约，买多6张合约，第一步先进行抵消操作，6张多单全部抵消完，只计算15张空单合约的委托保证金
2.持有空仓10张合约。卖空15张合约，买多13张合约，第一步先进行抵消操作，13张多单抵消后还剩3张买多合约，然后再按之前的计算规则3<15,结果=3张多单合约的委托保证金+12张(15-3)空单合约的委托保证金
3.持有空仓10张合约。卖空15张合约，买多27张合约，第一步先进行抵消操作，27张多单抵消后还剩17(27-10)张买多合约，然后再按之前的计算规则17>15, 只计算17张多单合约的委托保证金


盈亏计算：合约数量 * 乘数 * (100000000/开仓价格 - 100000000/平仓价格)


仓位相关参数
目前仓位(合约)数量: 多个成交累加
开仓价值(界面没有显示): 多个成交(价值)累加
价值(当前): 100000000/标记价格,结果四乘五入,再乘以仓位数量
开仓价格: 开仓价值/仓位数量,结果四乘五入,假设舍入后的结果为A,然后再100000000/A (开仓或者加仓需要计算，减仓的情况下不计算，维持之前不变)
标记价格: 实时统计
强平价格: (100000000/开仓价格-100000000/破产价格) * 仓位数量 = -(开仓保证金-维持保证金) 维持保证金: 0.50%+平仓佣金+资金费率
当前保证金: (开仓价值+开仓价值*开仓手续费率) / 杠杆倍数 + 平仓手续费(委托价值*平仓手续费率) + 未实现盈亏。特殊情况:如果是空仓一倍杠杆那保证金就等于当前价值
未实现盈亏: 开仓价值-价值(当前),多仓和空仓方向是反的
已实现盈亏:多个成交的手续费累加,外加每八小时的费率交换,外加减仓的收益


1 bitcoin (BTC)
= 1000 millibitcoins (mBTC)
= 1 million microbitcoins (uBTC) 也就是100 0000
= 100 million Satoshi 也就是1亿（10000 0000）

"""