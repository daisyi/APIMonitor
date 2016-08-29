#!/usr/bin/env python
# encoding: utf-8

import os
import json
import threading
import ConfigParser
from multiprocessing import Process
from time import sleep
from ringcentral.subscription import Events
from ringcentral.http.api_exception import ApiException
from ringcentral import SDK
import time
from threading import Event, Thread


import sys
import traceback
from optparse import OptionParser, OptionGroup
import socket
import logging
import random
import datetime
import time
import httplib
import urllib
import base64
import json
import string




logging.basicConfig(filename="log/LOG1",level=logging.DEBUG)

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

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
fileHandler = logging.FileHandler("{0}/{1}.log".format("log", "log"))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
log = logging

#Read Credentials from the file
config = ConfigParser.ConfigParser()
config.read('credentials.ini')
USERNAME = config.get('Credentials', 'USERNAME')
EXTENSION = config.get('Credentials', 'EXTENSION')
PASSWORD = config.get('Credentials', 'PASSWORD')
APP_KEY = config.get('Credentials', 'APP_KEY')
APP_SECRET = config.get('Credentials', 'APP_SECRET')
SERVER = config.get('Credentials', 'SERVER')
FFROM= config.get('Credentials','FFROM')
TTO= config.get('Credentials','TTO')

cache_dir = os.path.join(os.getcwd(), '_cache')
file_path = os.path.join(cache_dir, 'platform.json')


SUBSCRIPTION_PREFIX = "/restapi/v1.0/account/~/extension"

PRESENCE_STATUS_TEMPLATE = """<?xml version=\"1.0\"?>
<presence version=\"1.0\">
<user entity=\"blf%(mailBoxId)s\">
<status state=\"%(telephonyStatus)s\" id=\"%(sequenceId)d\" source=\"%(sourceId)s\">
<call presence.cseq=\"%(cseq)s\" owner=\"%(sourceId)s\" direction=\"initiator\" rc-session-id=\"1234567\"/>
</status>
</user>
</presence>"""


class SubscriptionType:
    PRESENCE = "/~/presence?detailedTelephonyState=true"
    AGGREGATED_PRESENCE = "/~/presence?aggregated=true&detailedTelephonyState=true"
    MESSAGE_STORE = "/~/message-store"
    EXTENSION = "/~"
    PRESENCE_LINES = "/~/presence/line"
    INCOMING_CALL = "/~/incoming-call-pickup"


def logger_func_args(f):
    def ret(*args, **kwards):
        log.info("E:{}(args = {} kwards = {})".format(f.__name__, args, kwards))
        f(*args, **kwards)
        log.info("L:{}(args = {} kwards = {})".format(f.__name__, args, kwards))
    return ret

def time_logger(f):
    def ret(*args, **kwards):
        now = datetime.datetime.now()
        res = f(*args, **kwards)
        log.info("{} : time spent {} sec.".format(f.__name__, (datetime.datetime.now() - now).total_seconds()))
        return res
    return ret


SUBSCRIPTION_NOTIFICATION = False
RINGOUT_CALL = False


class RepeatedTimer:
    """Repeat `function` every `interval` seconds."""
    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target)
        self.thread.start()
        log.info("New run initiated")

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self):
        self.event.set()
        self.thread.join()


def get_file_cache():
    try:
        f = open(file_path, 'r')
        data = json.load(f)
        f.close()
        return data if data else {}
    except IOError:
        return {}


def set_file_cache(cache):
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)
    f = open(file_path, 'w')
    json.dump(cache, f, indent=4)
    f.close()


cache = get_file_cache()

# Create SDK instance
sdk = SDK(APP_KEY, APP_SECRET, SERVER)
platform = sdk.platform()

# Set cached authentication data
platform.auth().set_data(cache)


def login():
    try:
        platform.is_authorized()
        log.info('Authorized already by cached data')
    except Exception as e:
        authorize_response = platform.login(USERNAME, EXTENSION, PASSWORD)
        if all(k in authorize_response.response().json() for k in ("access_token", "refresh_token_expires_in",
                                                                   "expires_in", "token_type", "endpoint_id", "scope",
                                                                   "refresh_token_expires_in", "expires_in",
                                                                   "refresh_token", "owner_id")):
            log.info('Authorized by credentials')
            log.info(authorize_response.json_dict())

    set_file_cache(platform.auth().data())
    log.info("Authentication data has been cached")


def refresh():
    refresh_response =platform.refresh()
    if all(k in refresh_response.response().json() for k in (
    "access_token", "refresh_token_expires_in", "expires_in", "token_type", "endpoint_id", "scope",
    "refresh_token_expires_in", "expires_in", "refresh_token", "owner_id")):
        log.info('Refreshed by credentials')
        log.info(refresh_response.json_dict())

#CREATE RINGOUT CALL
def make_ringout(ffrom,tto,pprompt):

    body = {
        "from": {"phoneNumber": ffrom},
        "to": {"phoneNumber": tto},
        "callerId": {"phoneNumber": ''},
        "playPrompt": pprompt
    }
    # //self, url, body=None, query_params=None, headers=None, skip_auth_check=False
    response= platform.post(url="/account/~/extension/~/ringout",body=body)

    log.info("Make ringout from %(from_phone)s to %(to_phone)s" % {
        "from_phone": ffrom,
        "to_phone": tto,
        "status": response.json().status.callStatus
    })
    RINGOUT_CALL = True
    log.info(response.json_dict())


#SEND SMS
def send_sms(text, ffrom, to):
    rsp = platform.post("/restapi/v1.0/account/~/extension/~/sms", {
        "from": {"phoneNumber": ffrom},
        "to": [{"phoneNumber": to}],
        "text": text
    })
    msg_status = rsp.json_dict()
    log.info("Sending SMS from %(from_number)s to %(to_number)s: %(status)s" % {
        "from_number": ffrom,
        "to_number": to,
        "status": msg_status['messageStatus']
    })
    log.info(rsp.json_dict())
    log.error("SMS Sending failed" ) if msg_status['messageStatus'] == 'SendingFailed' else log.info("SMS sent :  OK")


#PAGER
def send_pager(text, ffrom, to):
    rsp = platform.post("/restapi/v1.0/account/~/extension/~/company-pager", {
        "from": {"extensionNumber": ffrom},
        "to": [{"extensionNumber": to}],
        "text": text
    })
    msg_status = rsp.json_dict()
    log.info("Sending Pager from %(from_ext)s to %(to_ext)s: %(status)s" % {
        "from_ext": ffrom,
        "to_ext": to,
        "status": msg_status['messageStatus']
    })
    log.info(rsp.json_dict())
    log.error("Pager Sending failed") if msg_status['messageStatus'] == 'SendingFailed' else log.info("Pager sent :  OK")

#EXTENSION DATA
def get_extension_info():
    extension_info = platform.get("/restapi/v1.0/account/~/extension/~/")
    # log.debug("Getting extension info %(extensionNumber)s" % {"extensionNumber": extension_info.extensionNumber})
    log.debug(extension_info.json_dict())

#CHANGE EXTENSION
def change_extension():
    log.info("Will change first name")
    set_first_name(randomword(10))


def set_first_name(firstname):
    data = \
        {
            "contact": {
                "firstName": firstname
            }
        }
    change_extension = platform.put("/restapi/v1.0/account/~/extension/~/", data)
    log.debug(change_extension.json_dict())


def randomword(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))


#RESETTING
def reset_flag():
    RINGOUT_CALL = False
    SUBSCRIPTION_NOTIFICATION = False

#RUN JOB EVERY 5 MIN
def run_job():

    send_sms("Montior: SMS Test", FFROM , "6197619503")
    time.sleep(5)
    send_pager("Montior: Pager Test",'101','102')
    time.sleep(5)
    get_extension_info()
    time.sleep(5)
    change_extension()
    time.sleep(5)
    make_ringout(FFROM, TTO, "false")
    time.sleep(2)
    if (RINGOUT_CALL==SUBSCRIPTION_NOTIFICATION)==True:
       log.info("Subscription working as expected")
    else:
        log.CRITICAL("No Subscription Events for Presence")
    reset_flag()


def threaded_run(func, publisher_key, subscriber_key, channel, encryption_key=None, default=None):
    class InterruptableThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.daemon = True
            self.result = default
            self.exc_info = (None, None, None)

        def run(self):
            try:
                self.result = func(publisher_key, subscriber_key, channel, encryption_key)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
                self.exc_info = sys.exc_info()

        def suicide(self):
            raise RuntimeError('Stop has been called')

    it = InterruptableThread()
    it.start()
    return it


def join_thread(it, timeout):
    it.join((int)(timeout))
    if it.exc_info[0] is not None:  # if there were any exceptions
        a, b, c = it.exc_info
        raise a, b, c  # communicate that to caller
    if it.isAlive():
        try:
            it.suicide()
        except RuntimeError:
            traceback.print_exc(file=sys.stdout)
            raise RuntimeError(
                "Timed out after %(d)r seconds. Check your installation for errors or increase timeout interval" %
                {'d': timeout})
    else:
        return it.result


def main():

    # Check authentication
    login()

    # Perform refresh by force
    refresh()

    #run background job for different api endpoints
    run_job()
    timer = RepeatedTimer(300, run_job)

    # Pubnub notifications example
    def on_message(msg):
        SUBSCRIPTION_NOTIFICATION = True
        if all(k in msg for k in ("uuid", "event","timestamp","subscriptionId","body")):
            log.info(msg)
        else:
            log.error("Subscription not behaving as expected. Please check the log file for further information.")
            log.error(msg)

    def pubnub():
        try:
            s = sdk.create_subscription()
            s.add_events(['/account/~/extension/~/presence'])
            s.on(Events.notification, on_message)
            s.register()


            while True:
                sleep(0.1)
        except KeyboardInterrupt:
            log.CRITICAL("Pubnub listener stopped...")

    p = Process(target=pubnub)
    try:
        p.start()
    except KeyboardInterrupt:
        p.terminate()
        timer.stop()
        log.CRITICAL("Stopped by User")
    log.info("Wait for notification...")


if __name__ == '__main__':
    main()