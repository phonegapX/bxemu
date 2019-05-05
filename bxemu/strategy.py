# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from six import with_metaclass


class StrategyTemplate(with_metaclass(ABCMeta)):
    """
    策略模板
    """

    def __init__(self, pm):
        """Constructor"""
        self.pm = pm
        
    @abstractmethod
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        pass

    @abstractmethod
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        pass
    
    @abstractmethod
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass
    
    @abstractmethod
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        pass