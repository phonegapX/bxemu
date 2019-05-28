# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals
from future.builtins import bytes, chr, dict, int, range, str
from future.utils import iteritems
from future.standard_library import hooks

import sys
try:
    reload         # Python 2
    reload(sys)
    sys.setdefaultencoding('utf8')
except NameError:  # Python 3
    from importlib import reload
    reload(sys)

import websocket
import threading
import traceback
import ssl
from time import sleep
import json
import time
import hashlib
import hmac
import decimal
import logging
from decimal import Decimal
import sqlite3
import multiprocessing
import atexit
import signal

with hooks():  # Python 2/3 compat
    from urllib.parse import urlparse, urlunparse

import rootpath


class settings():pass
settings.API_KEY = ""
settings.API_SECRET = ""


def setup_custom_logger(name, log_level=logging.DEBUG):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(handler)
    return logger

# Generates an API signature.
# A signature is HMAC_SHA256(secret, verb + path + nonce + data), hex encoded.
# Verb must be uppercased, url is relative, nonce must be an increasing 64-bit integer
# and the data, if present, must be JSON without whitespace between keys.
#
# For example, in psuedocode (and in real code below):
#
# verb=POST
# url=/api/v1/order
# nonce=1416993995705
# data={"symbol":"XBTZ14","quantity":1,"price":395.01}
# signature = HEX(HMAC_SHA256(secret, 'POST/api/v1/order1416993995705{"symbol":"XBTZ14","quantity":1,"price":395.01}'))
def generate_signature(secret, verb, url, nonce, data):
    """Generate a request signature compatible with BitMEX."""
    # Parse the url so we can remove the base and extract just the path.
    parsedURL = urlparse(url)
    path = parsedURL.path
    if parsedURL.query:
        path = path + '?' + parsedURL.query
    if isinstance(data, (bytes, bytearray)):
        data = data.decode('utf8')
    # print "Computing HMAC: %s" % verb + path + str(nonce) + data
    message = verb + path + str(nonce) + data
    signature = hmac.new(bytes(secret, 'utf8'), bytes(message, 'utf8'), digestmod=hashlib.sha256).hexdigest()
    return signature

def generate_expires():
    return int(time.time() + 3600)

# Connects to BitMEX websocket for streaming realtime data.
# The Marketmaker still interacts with this as if it were a REST Endpoint, but now it can get
# much more realtime data without heavily polling the API.
#
# The Websocket offers a bunch of data as raw properties right on the object.
# On connect, it synchronously asks for a push of all this data then returns.
# Right after, the MM can start using its data. It will be updated in realtime, so the MM can
# poll as often as it wants.
class BitMEXWebsocket(object):
    
    self = None #兼容python2和python3

    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 200

    def __init__(self):
        BitMEXWebsocket.self = self
        self.logger = setup_custom_logger('websocket', log_level=logging.DEBUG)
        self.__reset()
        self.timestamp = 0

    def __del__(self):
        self.exit()

    def connect(self, endpoint="", symbol="XBTUSD", shouldAuth=True):
        '''Connect to the websocket and initialize data stores.'''

        self.logger.debug("Connecting WebSocket.")
        self.symbol = symbol
        self.shouldAuth = shouldAuth

        # We can subscribe right in the connection querystring, so let's build that.
        # Subscribe to all pertinent endpoints
        #subscriptions = [sub + ':' + symbol for sub in ["quote", "trade"]]
        #subscriptions += ["instrument"]  # We want all of them
        subscriptions = ["instrument:" + symbol]
        if self.shouldAuth:
            subscriptions += [sub + ':' + symbol for sub in ["order", "execution"]]
            subscriptions += ["margin", "position"]

        # Get WS URL and connect.
        urlParts = list(urlparse(endpoint))
        urlParts[0] = urlParts[0].replace('http', 'ws')
        urlParts[2] = "/realtime?subscribe=" + ",".join(subscriptions)
        wsURL = urlunparse(urlParts)
        self.logger.info("Connecting to %s" % wsURL)
        self.__connect(wsURL)
        self.logger.info('Connected to WS. Waiting for data images, this may take a moment...')

        # Connected. Wait for partials
        self.__wait_for_symbol(symbol)
        if self.shouldAuth:
            self.__wait_for_account()
        self.logger.info('Got all market data. Starting.')

    #
    # Lifecycle methods
    #
    def error(self, err):
        self._error = err
        self.logger.error(err)
        self.exit()

    def exit(self):
        self.exited = True
        self.ws.close()

    #
    # Private methods
    #

    def __connect(self, wsURL):
        '''Connect to the websocket in a thread.'''
        self.logger.debug("Starting thread")

        ssl_defaults = ssl.get_default_verify_paths()
        sslopt_ca_certs = {'ca_certs': ssl_defaults.cafile}
        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error,
                                         header=self.__get_auth()
                                         )
        
        #self.wst = threading.Thread(target=lambda: self.ws.run_forever(sslopt=sslopt_ca_certs))
        self.wst = threading.Thread(target=lambda: self.ws.run_forever(sslopt=sslopt_ca_certs, http_proxy_host='127.0.0.1', http_proxy_port=7777))
        
        self.wst.daemon = True
        self.wst.start()
        self.logger.info("Started thread")

        # Wait for connect before continuing
        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout and not self._error:
            sleep(1)
            conn_timeout -= 1

        if not conn_timeout or self._error:
            self.logger.error("Couldn't connect to WS! Exiting.")
            self.exit()
            sys.exit(1)

    def __get_auth(self):
        '''Return auth headers. Will use API Keys if present in settings.'''

        if self.shouldAuth is False:
            return []

        self.logger.info("Authenticating with API Key.")
        # To auth to the WS using an API key, we generate a signature of a nonce and
        # the WS API endpoint.
        nonce = generate_expires()
        return [
            "api-expires: " + str(nonce),
            "api-signature: " + generate_signature(settings.API_SECRET, 'GET', '/realtime', nonce, ''),
            "api-key:" + settings.API_KEY
        ]

    def __wait_for_account(self):
        '''On subscribe, this data will come down. Wait for it.'''
        # Wait for the keys to show up from the ws
        while not {'margin', 'position', 'order'} <= set(self.data):
            sleep(0.1)

    def __wait_for_symbol(self, symbol):
        '''On subscribe, this data will come down. Wait for it.'''
        while not {'instrument', 'trade', 'quote'} <= set(self.data):
            sleep(0.1)
    
    @staticmethod
    def __on_message(self, message):
        '''Handler for parsing WS messages.'''
        self = BitMEXWebsocket.self
        
        message = json.loads(message)
        #self.logger.debug(json.dumps(message))

        table = message['table'] if 'table' in message else None
        action = message['action'] if 'action' in message else None
        try:
            if 'subscribe' in message:
                if message['success']:
                    self.logger.debug("Subscribed to %s." % message['subscribe'])
                else:
                    self.error("Unable to subscribe to %s. Error: \"%s\" Please check and restart." % (message['request']['args'][0], message['error']))
            elif 'status' in message:
                if message['status'] == 400:
                    self.error(message['error'])
                if message['status'] == 401:
                    self.error("API Key incorrect, please check and restart.")
            elif action:
                if table not in self.data:
                    self.data[table] = []

                if table not in self.keys:
                    self.keys[table] = []

                # There are four possible actions from the WS:
                # 'partial' - full table image
                # 'insert'  - new row
                # 'update'  - update row
                # 'delete'  - delete row
                if action == 'partial':
                    self.logger.debug("%s: partial" % table)
                    self.data[table] += message['data']
                    # Keys are communicated on partials to let you know how to uniquely identify
                    # an item. We use it for updates.
                    self.keys[table] = message['keys']
                elif action == 'insert':
                    self.logger.debug('%s: inserting %s' % (table, message['data']))
                    self.data[table] += message['data']

                    # Limit the max length of the table to avoid excessive memory usage.
                    # Don't trim orders because we'll lose valuable state if we do.
                    if table not in ['order', 'orderBookL2'] and len(self.data[table]) > BitMEXWebsocket.MAX_TABLE_LEN:
                        self.data[table] = self.data[table][(BitMEXWebsocket.MAX_TABLE_LEN // 2):]

                elif action == 'update':
                    #self.logger.debug('%s: updating %s' % (table, message['data']))
                    # Locate the item in the collection and update it.
                    for updateData in message['data']:
                        item = findItemByKeys(self.keys[table], self.data[table], updateData)
                        if not item:
                            continue  # No item found to update. Could happen before push

                        # Log executions
                        if table == 'order':
                            is_canceled = 'ordStatus' in updateData and updateData['ordStatus'] == 'Canceled'
                            if 'cumQty' in updateData and not is_canceled:
                                contExecuted = updateData['cumQty'] - item['cumQty']
                                if contExecuted > 0:
                                    instrument = self.get_instrument(item['symbol'])
                                    self.logger.info("Execution: %s %d Contracts of %s at %.*f" %
                                             (item['side'], contExecuted, item['symbol'],
                                              instrument['tickLog'], item['price']))

                        # Update this item.
                        item.update(updateData)

                        # Remove canceled / filled orders
                        if table == 'order' and item['leavesQty'] <= 0:
                            self.data[table].remove(item)

                        if 'lastPrice' in updateData:
                            curTimestamp = int(time.time())
                            if curTimestamp - self.timestamp > 60:  #间隔超过一分钟才记录
                                self.timestamp = curTimestamp
                                self.logger.debug('========== %s : %s : %s ==========' % (item['lastPrice'], item['markPrice'], item['timestamp']))
                                self.recorder.record(item['lastPrice'], item['markPrice'], item['timestamp'])

                elif action == 'delete':
                    self.logger.debug('%s: deleting %s' % (table, message['data']))
                    # Locate the item in the collection and remove it.
                    for deleteData in message['data']:
                        item = findItemByKeys(self.keys[table], self.data[table], deleteData)
                        self.data[table].remove(item)
                else:
                    raise Exception("Unknown action: %s" % action)
        except:
            self.logger.error(traceback.format_exc())

    @staticmethod
    def __on_open(self):
        self = BitMEXWebsocket.self
        self.logger.debug("Websocket Opened.")
        self.recorder = self.clsDataRecord()
        self.recorder.open()

    @staticmethod
    def __on_close(self):
        self = BitMEXWebsocket.self
        self.logger.info('Websocket Closed')
        self.exit()
    
    @staticmethod
    def __on_error(self, error):
        self = BitMEXWebsocket.self
        if not self.exited:
            self.error(error)

    def __reset(self):
        self.data = {}
        self.keys = {}
        self.exited = False
        self._error = None

    def setRecorder(self, cls):
        self.clsDataRecord = cls

def findItemByKeys(keys, table, matchData):
    for item in table:
        matched = True
        for key in keys:
            if item[key] != matchData[key]:
                matched = False
        if matched:
            return item

class DataRecord(object):

    def __init__(self):
        pass
    
    def open(self):
        dbfile = rootpath.join_relative_path("marketquote.db")
        self.conn = sqlite3.connect(dbfile)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS t_market
                    (id INTEGER PRIMARY KEY,
                     f_lastprice TEXT NOT NULL,
                     f_markprice TEXT NOT NULL,
                     f_timestamp TEXT NOT NULL
                      );''')
        self.conn.commit()
    
    def close(self):
        self.conn.close()
    
    def record(self, lastPrice, markPrice, timestamp):
        timestamp = timestamp.replace('T', ' ')
        timestamp = timestamp[0:timestamp.rfind('.')]
        self.cursor.execute("INSERT INTO t_market (f_lastprice, f_markprice, f_timestamp) VALUES ('%s', '%s', '%s')" % (lastPrice, markPrice, timestamp));
        self.conn.commit()

def runChildProcess():
    ws = BitMEXWebsocket()
    ws.setRecorder(DataRecord)
    ws.connect("https://testnet.bitmex.com/api/v1", shouldAuth=False)
    while(ws.ws.sock.connected):
        sleep(1)

childProcess = None

def exit():
    global childProcess
    childProcess.terminate()
    sys.exit()

if __name__ == "__main__":
    atexit.register(exit)
    signal.signal(signal.SIGTERM, exit)
    while(True):
        childProcess = multiprocessing.Process(target=runChildProcess)
        childProcess.start()
        print('子进程启动成功')
        childProcess.join()
        sleep(1)