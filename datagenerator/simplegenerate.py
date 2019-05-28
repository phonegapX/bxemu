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
from decimal import Decimal

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import bxemu.util as util
import rootpath


def toNearest(num, tickSize):
    """Given a number, round it to the nearest tick. Very useful for sussing float error
       out of numbers: e.g. toNearest(401.46, 0.01) -> 401.46, whereas processing is
       normally with floats would give you 401.46000000000004.
       Use this after adding/subtracting/multiplying numbers."""
    tickDec = Decimal(str(tickSize))
    return float((Decimal(round(num / tickSize, 0)) * tickDec))

#模拟开始时间
startDt = datetime.datetime.strptime("2019-5-1 0:0:0", "%Y-%m-%d %H:%M:%S")
#模拟结束时间
endDt = datetime.datetime.strptime("2019-5-3 23:59:59", "%Y-%m-%d %H:%M:%S")
diff = endDt - startDt
minutes = int(round(diff.total_seconds()/60))

S0 = 5000       #初始价格
r = 0.00        #无风险收益
sigma = 0.07    #模拟周期内的波动率
T = 1.0
I = 100         #模拟100条价格路径
M = minutes     #时间周期
dt = T/M
S = np.zeros((M, I))
S[0] = S0
for t in range(1, M):
    S[t] = S[t-1] * np.exp((r-0.5*sigma**2)*dt + sigma*np.sqrt(dt)*np.random.standard_normal(I))
    
#输出直方图
plt.hist(S[-1], bins=50)
plt.xlabel('price')
plt.ylabel('frequency')
plt.show()

#价格走势图
plt.plot(S[:,:], lw=1.5)
plt.xlabel('time')
plt.ylabel('price')
plt.show()

#在生成的100条价格路径中随机选择一条
index = random.randint(0, 99)
vfun = np.vectorize(toNearest)
l = vfun(S[:, index], 0.5)
#生成模拟时间序列
t = []
while startDt < endDt:
    t.append(startDt.strftime("%Y-%m-%d %H:%M:%S"))
    print(startDt.strftime("%Y-%m-%d %H:%M:%S"))
    startDt = startDt + datetime.timedelta(minutes=1)

#构造DataFrame
ser_list = dict()
ser_list["price"] = pd.Series(data=l, index=None, dtype=float, name="price")
ser_list["time"] = pd.Series(data=t, index=None, dtype=str, name="time")
df = pd.DataFrame(ser_list)
df.index.name = 'index'
print(df)
print(df.info())
print(df.describe())

#输出选中的这条价格路径的图形走势
plt.plot(l, lw=1.5)
plt.xlabel('time')
plt.ylabel('price')
plt.show()

#保存到csv文件
df.to_csv(rootpath.join_relative_path("marketquote.csv"))