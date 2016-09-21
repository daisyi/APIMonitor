import time
import re
import os
import stat
import gzip
import logging
import logging.handlers as handlers


class TimedRotatingLog(logging.handlers.TimedRotatingFileHandler):
    """ My rotating file hander to compress rotated file """

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None,
                 delay=0, when='h', interval=1, utc=False):
        if maxBytes > 0:
            mode = 'a'
        logging.handlers.TimedRotatingFileHandler.__init__(
            self, filename, when, interval, backupCount, encoding, delay, utc)
        self.maxBytes = maxBytes
        self.backupCount = backupCount

    def shouldRollover(self, record):
        """ Determine if rollover should occur. """
        # Check rollover by size
        if self.stream is None:  # delay was set...
            self.stream = self._open()
        if self.maxBytes > 0:  # are we rolling over?
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)  # due to non-posix-compliant Windows feature
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return 1
        # Check rollover by time
        t = int(time.time())
        if t >= self.rolloverAt:
            return 1
        return 0

    def rotate(self, source, dest):
        """ Compress rotated log file """
        os.rename(source, dest)
        f_in = open(dest, 'rb')
        f_out = gzip.open("%s.gz" % dest, 'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        os.remove(dest)