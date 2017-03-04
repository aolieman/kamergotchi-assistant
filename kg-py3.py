# Kamergotchi Automator
# https://github.com/MartienB/kamergotchi-automator
# Developed by: Martien Bonfrer
# Date: 20/2/17

from urllib.parse import urlencode
from urllib.request import Request, urlopen
import ssl
import time
import json
import urllib.request
from urllib.parse import urljoin
from urllib.error import URLError
from urllib.error import HTTPError
import codecs
import random
import datetime
import logging
from numpy.random import lognormal
from pprint import pprint
from functools import wraps

from secret import PLAYER_ID, SLEEP_INTERVAL


logger = logging.getLogger()

player_token = PLAYER_ID
bedtime, waketime = SLEEP_INTERVAL

base_headers = {
    'User-Agent': "okhttp/3.4.1",
    'Host': "api.kamergotchi.nl",
    'accept': "application/json, text/plain, */*",
    'Connection': "close"
}

last_action_time = datetime.datetime.utcnow()


def timed_action(func):
    """
    Keep track of when the last action was taken
    """
    @wraps(func)
    def wrapped_action(*args, **kwargs):
        global last_action_time
        last_action_time = datetime.datetime.utcnow()
        return func(*args, **kwargs)
        
    return wrapped_action
    


def getInfo(player_token):
    url = 'https://api.kamergotchi.nl/game'
    headers = base_headers.copy()
    headers['x-player-token'] = player_token
    
    request = Request(url, headers=headers)

    context = ssl._create_unverified_context() # There is something wrong with the ssl certificate, so we just ignore it!
    try:
        json = urlopen(request, context=context).read().decode()
    except HTTPError:
        logger.exception('Info Error:')
        time.sleep(2)
        return getInfo(player_token)

    return json

    
def giveMostNeededCare(player_token):
    returnJson = json.loads(getInfo(player_token))
    game = returnJson['game']
    careLeft = game['careLeft']
    current = game['current']
    full_health = min(current.values()) == 100

    foodValue = current['food']
    attentionValue = current['attention']
    knowledgeValue = current['knowledge']

    careReset = game['careReset']
    claimReset = game['claimReset']

    careResetDate = datetime.datetime.strptime(careReset, "%Y-%m-%dT%H:%M:%S.%fZ")
    claimResetDate = datetime.datetime.strptime(claimReset, "%Y-%m-%dT%H:%M:%S.%fZ")
    now = datetime.datetime.utcnow()

    # check if there are cares left, or if the careResetDate has elapsed (careLeft stays 0 even after reset date)
    wait_seconds = 0
    if not full_health and (careLeft > 0 or now > careResetDate):

        if (foodValue < attentionValue):
            if (knowledgeValue < foodValue):
                giveCare(player_token, 'knowledge');
            else:
                giveCare(player_token, 'food')
            
        else:
            if (attentionValue < knowledgeValue):
                giveCare(player_token, 'attention')
            else:
                giveCare(player_token, 'knowledge')
    elif (now > claimResetDate):
        # time to claim the bonus
        claimBonus(player_token)
        pprint(game)
    elif full_health:
        wait_seconds = 1
    else:
        wait_seconds = (careResetDate-now).total_seconds()
        progress('Not yet! Remaining seconds: {}'.format(wait_seconds))
        
    return wait_seconds
    

@timed_action
def claimBonus(player_token):
    context = ssl._create_unverified_context() 
    sessionUrl = 'https://api.kamergotchi.nl/game/claim'

    headers = base_headers.copy()
    headers['x-player-token'] = player_token

    req = urllib.request.Request(sessionUrl, headers=headers, method='POST')

    try: 
        response = urllib.request.urlopen(req, context=context)
        jsonresp = response.read().decode()
        
        progress('Succesfully claimed bonus!')
    except HTTPError as httperror:
        logger.exception('Claim Error:')
    except URLError as urlerror:
        logger.exception('Claim Error:')
    except:
        logger.exception('Unexpected Claim Error:')


@timed_action
def giveCare(player_token, careType):   
    context = ssl._create_unverified_context() 
    sessionUrl = 'https://api.kamergotchi.nl/game/care'
    reqBody = {'bar' : careType}

    data = json.dumps(reqBody, separators=(',', ':')).encode('utf-8')

    headers = base_headers.copy()
    headers['x-player-token'] = player_token
    headers['Content-type'] = "application/json;charset=utf-8"

    req = urllib.request.Request(sessionUrl, data, headers, method='POST')

    try: 
        response = urllib.request.urlopen(req, context=context)
        jsonresp = response.read().decode()

        returnJson = json.loads(jsonresp)
        game = returnJson['game']
        progress('{}{}{}{}{}'.format('Succesfully cared: ', careType, '(score: ', game['score'], ')'))
    except HTTPError as httperror:
        logger.exception('Care Error:')
    except URLError as urlerror:
        logger.exception('Care Error:')
    except:
        logger.exception('Unexpected Care Error:')

        
def progress(msg):
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print('{} -- {}'.format(now_str, msg))
    
    
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
    
    
def sleep_until(wakeup_dt, perturbation):
    utcnow = datetime.datetime.utcnow()
    delta_till = wakeup_dt - utcnow
    if random.random() < 0.67:
        delta_till += datetime.timedelta(seconds=perturbation)
    else:
        delta_till -= datetime.timedelta(seconds=perturbation)
    
    snooze = delta_till.seconds
    progress('Be back at {:%Y-%m-%d %H:%M:%S}\n'.format(utc_to_local(utcnow + delta_till)))
    time.sleep(snooze)
    
    
def ceil_dt(dt, delta):
    return dt + (datetime.datetime.min - dt) % delta
    
    
def get_next_dt():
    next_half_hour = ceil_dt(datetime.datetime.utcnow(), datetime.timedelta(minutes=30))
    if next_half_hour.minute == 0:
        return next_half_hour + datetime.timedelta(minutes=30)
    else:
        return next_half_hour
        

if __name__ == '__main__':
    # one time next_dt init to 6 minutes ago
    next_dt = datetime.datetime.utcnow() - datetime.timedelta(minutes=6)

    while True:
        now = datetime.datetime.now()
        if bedtime < now.hour < waketime:
            progress('ZzZzZzZ')
            next_dt = get_next_dt()
            sleep_until(next_dt, liv)
        else:
            long_intervals = (lognormal(0, 2, size=10) + 1) * 2

            for liv in long_intervals:
                short_intervals = lognormal(0, 1, size=30) / 2
                
                wait = 0
                for siv in short_intervals:
                    try:
                        wait = giveMostNeededCare(player_token)
                        if wait:
                            break
                    except (HTTPError, URLError):
                        logger.exception('Connection issue:')
                        progress('Retrying in {} seconds'.format(wait + siv))
                        
                    time.sleep(wait + siv)
                
                utcnow = datetime.datetime.utcnow()
                if wait is 1 and (
                    (last_action_time > next_dt)
                    or (utcnow > next_dt + datetime.timedelta(minutes=9))
                ):
                    next_dt = get_next_dt()
                    sleep_until(next_dt, liv)
                else:
                    snooze = wait + min(liv, 367.67)
                    progress('Be back in {} seconds'.format(snooze))
                    time.sleep(snooze)
                

