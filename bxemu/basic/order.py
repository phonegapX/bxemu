# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import unicode_literals

from datetime import datetime

from bxemu.constant import *
from bxemu.util.sequence import SequenceGenerator


class Order(object):
    """
    订单数据类
    """
    sg = SequenceGenerator()

    def __init__(self):
        """Constructor"""
        self.orderId = Order.sg.get_next('order')   #订单ID
        self.side = EMPTY_UNICODE   #委托方向
        self.price = EMPTY_FLOAT    #委托价格
        self.size = EMPTY_INT       #委托数量
        self.type = EMPTY_UNICODE   #委托类型
        self.time = datetime.now()  #委托时间
        self.left = EMPTY_INT       #委托剩余数量
        self.status = EMPTY_UNICODE

    @classmethod
    def create(cls, side, price, size, type):
        order = cls()
        order.side = side
        order.price = price
        order.size = size
        order.type = type
        order.left = size
        order.status = "New"
        return order

    @property
    def value(self):
        """
        委托价值
        """
        return round(100000000/self.price)*self.left
    