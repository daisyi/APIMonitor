import os
import json
import threading
import ConfigParser
import threading
from multiprocessing import Process
from time import sleep
from ringcentral.subscription import Events
from ringcentral.http.api_exception import ApiException
from ringcentral import SDK
from threading import Event, Thread
import sys
import traceback
import logger
import random
import datetime
import time
import json
import string



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
RINGOUT_SLEEP_TIME = int (config.get('Credentials','RINGOUT_SLEEP_TIME'))
RUN_JOB_TIME= int (config.get('Credentials','RUNTIME'))


cache_dir = os.path.join(os.getcwd(), '_cache')
file_path = os.path.join(cache_dir, 'platform.json')


log= logger.logging

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
        log.debug("New run initiated")

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self):
        self.event.set()
        self.thread.join()

class AtomicCounter:

    def __init__(self, initial=0):
        """Initialize a new atomic counter to given initial value (default 0)."""
        self.value = initial
        self._lock = threading.Lock()

    def increment(self, num=1):
        """Atomically increment the counter by num (default 1) and return the
        new value.
        """
        with self._lock:
            self.value += num
            return self.value

    def reset(self):
        with self._lock:
            self.value = 0
            return self.value

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
        os.system('chmod 777 -R _cache')
    f = open(file_path, 'w')
    json.dump(cache, f, indent=4)
    f.close()

cache = get_file_cache()

__counter__ = AtomicCounter(0)
__check_Count = 0


# Create SDK instance
sdk = SDK(APP_KEY, APP_SECRET, SERVER)
platform = sdk.platform()

# Set cached authentication data
platform.auth().set_data(cache)

def login():
    try:
        platform.is_authorized()
        log.debug('Authorized already by cached data')
    except Exception as e:
        authorize_response = platform.login(USERNAME, EXTENSION, PASSWORD)

        if(authorize_response.response().status_code):
            if all(k in authorize_response.response().json() for k in ("access_token", "refresh_token_expires_in",
                                                                   "expires_in", "token_type", "endpoint_id", "scope",
                                                                   "refresh_token_expires_in", "expires_in",
                                                                   "refresh_token", "owner_id")):
                log.debug('Authorized by credentials')
                log.debug(authorize_response.json_dict())
        else:
            log.critical("Login Failure. Please fix the application as soon as possible and restart the application")

    set_file_cache(platform.auth().data())
    log.debug("Authentication data has been cached")

def refresh():
    try:
        refresh_response =platform.refresh()
        if all(k in refresh_response.response().json() for k in (
        "access_token", "refresh_token_expires_in", "expires_in", "token_type", "endpoint_id", "scope",
        "refresh_token_expires_in", "expires_in", "refresh_token", "owner_id")):
            log.debug('Refreshed by credentials')
            log.debug(refresh_response.json_dict())
    except:
        log.critical("Refreshing Failed. Logged in with the new token.")
        login()

def pubnub():
    try:
        s = sdk.create_subscription()
        s.add_events(['/account/~/extension/~/presence'])
        s.on(Events.notification, on_message)
        s.register()
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        log.critical("Pubnub listener stopped...")

def pubnub_start():
    p = threading.Thread(target=pubnub)
    try:
        p.start()
    except KeyboardInterrupt:
        p.terminate()
    return p

# Pubnub notifications
def on_message(msg):
    try:
        update_Counter()
        log.debug(msg)
    except:
        log.critical("Subscription not behaving as expected. Please check the log file for further information.")

def resetting():
    global __counter__
    global __check_Count
    newcount = __counter__.reset()
    __check_Count = 0

def update_Counter():
    global __counter__
    global __check_Count
    __check_Count = __counter__.increment()



#Check the working of the subscription
def check_Result():
    log.debug('checking result')
    try:
        i = int (__check_Count)
        if i == 3 :
            log.debug("Subscription working as expected")
        elif i == 1 or i == 2:
            log.critical("Missing notifications in Subscription")
        elif i == 0:
            log.critical("Subscription is not working as expected. Please check the logs for more information.")
        else:
            log.critical("Counter is broken. Please contact the admin.")
    except:
        log.critical('Exception Occured in the Check Result. Please check the logs for more information.')
    finally:
        resetting()


#CREATE RINGOUT CALL
def make_ringout(ffrom,tto,pprompt):
    body = {
        "from": {"phoneNumber": ffrom},
        "to": {"phoneNumber": tto},
        "callerId": {"phoneNumber": ''},
        "playPrompt": pprompt
    }
    response= platform.post(url="/account/~/extension/~/ringout",body=body)
    log.debug(response.json_dict())
    return  response

#SEND SMS
def send_sms(text, ffrom, to):
    rsp = platform.post("/restapi/v1.0/account/~/extension/~/sms", {
        "from": {"phoneNumber": ffrom},
        "to": [{"phoneNumber": to}],
        "text": text
    })
    msg_status = rsp.json_dict()
    log.debug("Sending SMS from %(from_number)s to %(to_number)s: %(status)s" % {
        "from_number": ffrom,
        "to_number": to,
        "status": msg_status['messageStatus']
    })
    log.debug(rsp.json_dict())
    log.error("SMS Sending failed" ) if msg_status['messageStatus'] == 'SendingFailed' else log.info("SMS sent :  OK")

#PAGER
def send_pager(text, ffrom, to):
    rsp = platform.post("/restapi/v1.0/account/~/extension/~/company-pager", {
        "from": {"extensionNumber": ffrom},
        "to": [{"extensionNumber": to}],
        "text": text
    })
    msg_status = rsp.json_dict()
    log.debug("Sending Pager from %(from_ext)s to %(to_ext)s: %(status)s" % {
        "from_ext": ffrom,
        "to_ext": to,
        "status": msg_status['messageStatus']
    })
    log.debug(rsp.json_dict())
    log.error("Pager Sending failed") if msg_status['messageStatus'] == 'SendingFailed' else log.info("Pager sent :  OK")

#EXTENSION DATA
def get_extension_info():
    extension_info = platform.get("/restapi/v1.0/account/~/extension/~/")
    log.debug(extension_info.json_dict())

def randomword(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

#CHANGE EXTENSION
def change_extension():
    log.debug("Will change first name")
    set_first_name(randomword(10))

#EDIT EXTENSION
def set_first_name(firstname):
    data = \
        {
            "contact": {
                "firstName": firstname
            }
        }
    change_extension = platform.put("/restapi/v1.0/account/~/extension/~/", data)
    log.debug(change_extension.json_dict())


#RUN JOB MANAGER --- ADD NEW API CALLS TO THE JOB WHEN REQUIRED
def run_Job():
    send_sms("Montior: SMS Test", FFROM , "15856234138")
    time.sleep(5)
    send_pager("Montior: Pager Test",'101','102')
    time.sleep(5)
    get_extension_info()
    time.sleep(5)
    change_extension()
    time.sleep(5)
    set_first_name("TESTER")
    time.sleep(5)
    check_Ringout_Subscription()
    check_Result()


def check_Ringout_Subscription():
    make_ringout(FFROM, TTO, "false")
    time.sleep(RINGOUT_SLEEP_TIME)


def main():

    # Check authentication
    login()

    # Perform refresh by force
    refresh()

    #Start Subscription
    pubnub_start()

    #Run RingOut Every X Min
    timer = RepeatedTimer(RUN_JOB_TIME, run_Job)


if __name__ == '__main__':
    main()