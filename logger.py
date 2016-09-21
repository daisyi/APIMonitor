import logging
import sys


from TimedRotatingLog import TimedRotatingLog

# from logging.handlers import TimedRotatingFileHandler

import json
import os

logging.basicConfig(filename="log/LOG1",level=logging.DEBUG)


handler = TimedRotatingLog(filename="log/Monitor",maxBytes=5242880,backupCount=5,encoding="utf8",when="S",interval= 120)
handler.setLevel(logging.NOTSET)


logging.basicConfig(
     filename='checker.log',
     level=logging.NOTSET,
     format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
     datefmt='%Y-%m-%d %H:%M:%S'
 )

# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)
logging.getLogger('').addHandler(handler)
logger = logging.getLogger(__name__)



LEVELS = {'debug': logging.DEBUG,
		  'info': logging.INFO,
		  'warning': logging.WARNING,
		  'error': logging.ERROR,
		  'critical': logging.CRITICAL}

if len(sys.argv) > 1:
	level_name = sys.argv[1]
	level = LEVELS.get(level_name, logging.NOTSET)
	logging.basicConfig(level=level)

from logging.handlers import SocketHandler, DEFAULT_TCP_LOGGING_PORT
socketh = SocketHandler('localhost', DEFAULT_TCP_LOGGING_PORT)
logging.getLogger('').addHandler(socketh)

try:
	import http.client as http_client
except ImportError:
	# Python 2
	import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.


logFormatter = logging.Formatter('%(levelname)s: %(asctime)s %(funcName)s(%(lineno)d) -- %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
rootLogger = logging.getLogger("requests.packages.urllib3")
rootLogger.propagate = False
rootLogger.setLevel(logging.NOTSET)
fileHandler = logging.FileHandler("{0}/{1}.log".format("log", "log"))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.addHandler(handler)

# log = logging'



import logging
import sys


import TimedRotatingLog

from logging.handlers import TimedRotatingFileHandler
logging.basicConfig(filename="log/LOG1",level=logging.DEBUG)

handler = TimedRotatingFileHandler("log/Logger",
								   when="m",
								   interval=60,
								   backupCount=5)

LEVELS = {'debug': logging.DEBUG,
		  'info': logging.INFO,
		  'warning': logging.WARNING,
		  'error': logging.ERROR,
		  'critical': logging.CRITICAL}

if len(sys.argv) > 1:
	level_name = sys.argv[1]
	level = LEVELS.get(level_name, logging.NOTSET)
	logging.basicConfig(level=level)

from logging.handlers import SocketHandler, DEFAULT_TCP_LOGGING_PORT
socketh = SocketHandler('localhost', DEFAULT_TCP_LOGGING_PORT)
logging.getLogger('').addHandler(socketh)

try:
	import http.client as http_client
except ImportError:
	# Python 2
	import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.


logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger("requests.packages.urllib3")
rootLogger.propagate = True
rootLogger.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler("{0}/{1}.log".format("log", "log"))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.addHandler(handler)
#
# # log = logging