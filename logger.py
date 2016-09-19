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

# log = logging