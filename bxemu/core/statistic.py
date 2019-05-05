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


class Record(object):
    
    def __init__(self):
        """Constructor"""
        self.op = EMPTY_UNICODE
        self.leverageType = EMPTY_INT
        self.walletBalance = EMPTY_FLOAT     #钱包余额
        self.orderMargin = EMPTY_FLOAT       #委托保证金
        self.posSide = EMPTY_UNICODE         #持仓方向(多仓或空仓)
        self.posSize = EMPTY_INT             #目前仓位数量
        self.posMargin = EMPTY_FLOAT         #当前仓位保证金
        self.posUnrealisedPNL = EMPTY_FLOAT  #当前仓位未实现盈亏
        self.posRealisedPNL = EMPTY_FLOAT    #当前仓位已实现盈亏
        self.trade = None


class Statistic(object):
    """
    结果数据统计
    """
    OP_WALLET_DEPOSIT      = "OP_WALLET_DEPOSIT"       #钱包充值
    OP_POSITION_OPEN       = "OP_POSITION_OPEN"        #开仓
    OP_POSITION_INCREASE   = "OP_POSITION_INCREASE"    #加仓
    OP_POSITION_DECREASE   = "OP_POSITION_DECREASE"    #减仓(包括了平仓操作或者平仓后自动反向开仓的操作)
    OP_POSITION_BANKRUPTCY = "OP_POSITION_BANKRUPTCY"  #爆仓

    def __init__(self):
        """Constructor"""
        self.records = []

    def log(self, op, pm, trade):
        r = Record()
        r.op = op
        if op == Statistic.OP_WALLET_DEPOSIT:
            r.walletBalance = pm.wallet.walletBalance
        elif op == Statistic.OP_POSITION_BANKRUPTCY:
            r.leverageType = pm.leverageType
            r.walletBalance = pm.wallet.walletBalance
            r.orderMargin = pm.wallet.orderMargin
        else:
            r.leverageType = pm.leverageType
            r.walletBalance = pm.wallet.walletBalance
            r.orderMargin = pm.wallet.orderMargin
            #
            r.trade = trade
            #
            if pm.position.isHolding():
                r.posSide = pm.position.side
                r.posSize = pm.position.size
                r.posMargin = pm.position.margin
                r.posUnrealisedPNL = pm.position.unrealisedPNL
                r.posRealisedPNL = pm.position.realisedPNL
        #
        self.records.append(r)