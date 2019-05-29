# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import unicode_literals

import math
from datetime import datetime

from bxemu.constant import *
from bxemu.util.sequence import SequenceGenerator


class Trade(object):
    """
    成交数据类
    """
    sg = SequenceGenerator()

    def __init__(self):
        """Constructor"""
        self.tradeID = Trade.sg.get_next('trade')    #成交编号
        self.side = EMPTY_UNICODE       #方向
        self.execQty = EMPTY_INT        #成交数量
        self.execPrice = EMPTY_FLOAT    #成交价格
        self.value = EMPTY_FLOAT        #价值
        self.feeRate = EMPTY_FLOAT      #佣金费率
        self.feePaid = EMPTY_FLOAT      #已付费用
        self.orderType = EMPTY_UNICODE  #委托种类
        self.orderQty = EMPTY_INT       #委托数量
        self.qtyLeft = EMPTY_INT        #未成交数量
        self.orderPrice = EMPTY_FLOAT   #委托价格
        self.orderId = EMPTY_INT        #委托ID
        self.tradeType = EMPTY_UNICODE  #
        self.time = datetime.now()      #成交时间

    @classmethod
    def create(cls, side, execQty, execPrice, orderType, orderQty, qtyLeft, orderPrice, orderId, tradeType, time):
        trade = cls()
        trade.side = side                                       #方向
        trade.execQty = execQty                                 #成交数量
        trade.execPrice = execPrice                             #成交价格
        trade.value = round(100000000/execPrice)*execQty        #成交价值
        trade.tradeType = tradeType                             #
        if trade.tradeType == TRADE_TYPE_MAKER:
            trade.feeRate = MAKER_FEE_RATE                      #佣金费率
        else:
            trade.feeRate = TAKER_FEE_RATE                      #佣金费率
        trade.feePaid = math.floor(trade.feeRate*trade.value)   #已付费用
        trade.orderType = orderType                             #委托种类
        trade.orderQty = orderQty                               #委托数量
        trade.qtyLeft = qtyLeft                                 #未成交数量
        trade.orderPrice = orderPrice                           #委托价格
        trade.orderId = orderId                                 #委托ID
        trade.time = time                                       #成交时间
        return trade
    
    def split(self, base):
        """
        将一个成交分割成两个成交
        """
        assert self.execQty > base        
        secondPart = self.execQty-base
        trade1 = Trade.create(self.side, base, self.execPrice, self.orderType, self.orderQty, 
                              self.qtyLeft+secondPart, self.orderPrice, self.orderId, self.tradeType, self.time)
        trade2 = Trade.create(self.side, secondPart, self.execPrice, self.orderType, self.orderQty, 
                              self.qtyLeft, self.orderPrice, self.orderId, self.tradeType, self.time)
        return trade1, trade2