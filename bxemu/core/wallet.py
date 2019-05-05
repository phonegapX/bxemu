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


class Wallet(object):
    """
    钱包数据类
    """
    
    def __init__(self):
        """Constructor"""
        self.clean()
    
    def clean(self):
        self.__walletBalance = EMPTY_FLOAT    #钱包余额 (存款+提款+已实现盈亏)
        self.__unrealisedPNL = EMPTY_FLOAT    #未实现盈亏 (所有未平仓合约的当前盈亏)
        self.__marginBalance = EMPTY_FLOAT    #保证金余额 (你在交易所的总权益。保证金余额=钱包余额+未实现盈亏) 
        self.__positionMargin = EMPTY_FLOAT   #仓位保证金 (保留你手持仓位所需的最低保证金要求。此数值为你持有的每种合约的开仓价值乘以其所需的维持保证金比率之和，并加上任何未实现的盈亏)
        self.__orderMargin = EMPTY_FLOAT      #委托保证金 (你的委托所需要的最小保证金额。此数值为你的每个委托价值乘以其所需的起始保证金比例之和)
        self.__availableBalance = EMPTY_FLOAT #可用余额 (你可以用于开仓的保证金。可用余额=保证金金额-委托保证金-仓位保证金)
    
    #===================================================
    #钱包余额
    #===================================================
    @property
    def walletBalance(self):
        return self.__walletBalance
    
    @walletBalance.setter
    def walletBalance(self, value):
        if value < 0:
            raise Exception("钱包余额不能为负数")
        self.__walletBalance = value

    #===================================================
    #未实现盈亏
    #===================================================
    @property
    def unrealisedPNL(self):
        return self.__unrealisedPNL
    
    @unrealisedPNL.setter
    def unrealisedPNL(self, value):
        self.__unrealisedPNL = value

    #===================================================
    #保证金余额
    #===================================================  
    @property
    def marginBalance(self):
        self.__marginBalance = self.walletBalance + self.unrealisedPNL
        if self.__marginBalance < 0:
            raise Exception("保证金余额不能为负数")
        return self.__marginBalance

    #===================================================
    #仓位保证金
    #===================================================  
    @property
    def positionMargin(self):
        return self.__positionMargin
    
    @positionMargin.setter
    def positionMargin(self, value):
        if value < 0:
            raise Exception("仓位保证金不能为负数")
        self.__positionMargin = value
    
    #===================================================
    #委托保证金
    #===================================================
    @property
    def orderMargin(self):
        return self.__orderMargin
    
    @orderMargin.setter
    def orderMargin(self, value):
        if value < 0:
            raise Exception("委托保证金不能为负数")
        self.__orderMargin = value

    #===================================================
    #可用余额
    #===================================================
    @property
    def availableBalance(self):
        self.__availableBalance = self.marginBalance - self.positionMargin - self.orderMargin
        #if self.__availableBalance < 0:
        #    raise Exception("可用余额不能为负数")
        return self.__availableBalance
