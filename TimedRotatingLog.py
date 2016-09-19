import time
import re
import os
import stat
import logging
import logging.handlers as handlers

class TimedRotatingLog(handlers.TimedRotatingFileHandler):

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None,
                 delay=0, when='h', interval=1, utc=False):
        if maxBytes > 0:
            mode = 'a'
        handlers.TimedRotatingFileHandler.__init__(
            self, filename, when, interval, backupCount, encoding, delay, utc)
        self.maxBytes = maxBytes

    def shouldRollover(self, record):
        if self.stream is None:
            self.stream = self._open()
        if self.maxBytes > 0:
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return 1
        t = int(time.time())
        if t >= self.rolloverAt:
            return 1
        return 0

    # def demo_SizedTimedRotatingFileHandler():
    #     log_filename = '/tmp/log_rotate'
    #     logger = logging.getLogger('MyLogger')
    #     logger.setLevel(logging.DEBUG)
    #     handler = SizedTimedRotatingFileHandler(
    #         log_filename, maxBytes=100, backupCount=5,
    #         when='s', interval=10,
    #         # encoding='bz2',  # uncomment for bz2 compression
    #     )
    #     logger.addHandler(handler)
    #     for i in range(10000):
    #         time.sleep(0.1)
    #         logger.debug('i=%d' % i)
    #
    # demo_SizedTimedRotatingFileHandler()