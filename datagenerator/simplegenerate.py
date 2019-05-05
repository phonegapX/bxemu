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

import time
import datetime
import random

import bxemu.util as util
import rootpath


seed = random.randint(5000, 5500)   #价格在5000到5500之间


def analogPrice():
    """
    简单模拟价格波动
    """
    global seed
    x = random.randint(1, 3)
    if x == 1:
        if seed < 5500:
            seed += 0.5
    elif x == 2:
        if seed > 5000:
            seed -= 0.5
    elif x == 3:
        pass
    return seed

listQuote = [analogPrice() for x in range(60*24*7)] #一周=60分钟×24小时×7天

print("High:%d  Low:%d  Total:%d"%(max(listQuote), min(listQuote), len(listQuote)))

util.save_pickle(listQuote, rootpath.join_relative_path("simple_quote.list"))

import matplotlib.pyplot as plt

#指定图形大小
plt.figure(figsize=(22, 18))

#画图
plt.plot(listQuote)

#标识标题及坐标轴信息
plt.title('simple quote')
plt.xlabel('minute passed')
plt.ylabel('simulated price')

#显示画图结果
plt.show()
