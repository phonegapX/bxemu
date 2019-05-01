#-*- coding:utf-8 –*-

from __future__ import unicode_literals

from datetime import datetime

from bxemu.constant import *


class Tick(object):
    """
    Tick行情数据类
    """

    def __init__(self):
        """Constructor"""
        self.lastMarkPrice = EMPTY_FLOAT   #当前合理标记价格
        self.lastFillPrice = EMPTY_FLOAT   #当前期货成交价格
        self.time = datetime.now()
        
    @classmethod
    def create(cls, lastMarkPrice, lastFillPrice):
        tick = cls()
        tick.lastMarkPrice = lastMarkPrice
        tick.lastFillPrice = lastFillPrice
        return tick
