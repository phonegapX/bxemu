# -*- coding: utf-8 -*-

from __future__ import unicode_literals

ORDER_TYPE_LIMIT = 'Limit'
ORDER_TYPE_MARKET = 'Market'
DIRECTION_SELL = 'sell'
DIRECTION_BUY  = 'buy'
TRADE_TYPE_TAKER = 'taker'
TRADE_TYPE_MAKER = 'maker'

EMPTY_UNICODE = ''
EMPTY_INT = 0
EMPTY_FLOAT = 0.0

MAKER_FEE_RATE = -0.00025
TAKER_FEE_RATE = 0.00075

MAINTENANCE_RATE = 0.005

FUNDING_RATE = 0.001346 #资金费率,如果为正数代表多仓要付给空仓钱,负数代表空仓要付给多仓钱,0代表互相不用给,这个会影响维持保证金的计算
#FUNDING_RATE = 0.000885 #资金费率,如果为正数代表多仓要付给空仓钱,负数代表空仓要付给多仓钱,0代表互相不用给,这个会影响维持保证金的计算
#FUNDING_RATE = 0.001071 #资金费率,如果为正数代表多仓要付给空仓钱,负数代表空仓要付给多仓钱,0代表互相不用给,这个会影响维持保证金的计算

TV_PERCENTAGE = 0   #有多少概率不能完全成交 >=0 and <=100, 0=0%, 1=1%, 2=2%,....., 99=99%, 100=100%

__all__ = ['ORDER_TYPE_LIMIT', 'ORDER_TYPE_MARKET', 'DIRECTION_SELL', 'DIRECTION_BUY', 'TRADE_TYPE_TAKER', 'TRADE_TYPE_MAKER', 'EMPTY_UNICODE', 'EMPTY_INT', 'EMPTY_FLOAT', 'MAKER_FEE_RATE', 'TAKER_FEE_RATE', 'MAINTENANCE_RATE', 'FUNDING_RATE', 'TV_PERCENTAGE']