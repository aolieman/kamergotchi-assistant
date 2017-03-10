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
from pprint import pformat
from functools import wraps
from operator import itemgetter

from secret import PLAYER_ID, SLEEP_INTERVAL, CLAIM_ONLY


logger = logging.getLogger('kamergotchi.player')
logger.handlers = []
lhand = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s -- %(message)s',
    "%Y-%m-%d %H:%M:%S"
)
lhand.setFormatter(formatter)
logger.addHandler(lhand)
logger.setLevel(logging.INFO)

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
    


def getInfo(player_token, retries=0):
    url = 'https://api.kamergotchi.nl/game'
    headers = base_headers.copy()
    headers['x-player-token'] = player_token
    
    request = Request(url, headers=headers)

    context = ssl._create_unverified_context() # There is something wrong with the ssl certificate, so we just ignore it!
    try:
        json_resp = urlopen(request, context=context).read().decode()
    except (HTTPError, URLError) as e:
        logger.error('Info Error: {}'.format(e))
        time.sleep(1 + 2 * retries)
        return getInfo(player_token, 1 + retries)

    resp_dict = json.loads(json_resp)
    game = resp_dict['game']
    if game.get('quotes'):
        progress(str(game['quotes']))
    game['care_reset_date'] = datetime.datetime.strptime(
        game['careReset'], 
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    game['claim_reset_date'] = datetime.datetime.strptime(
        game['claimReset'], 
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    return game

    
def giveMostNeededCare(player_token):
    game = getInfo(player_token)
    
    care_left = game['careLeft']
    current = game['current']
    full_health = min(current.values()) == 100
    if not full_health:
        progress(str(current))

    care_reset_date = game['care_reset_date']
    claim_reset_date = game['claim_reset_date']
    utcnow = datetime.datetime.utcnow()

    # claim bonus, or give care, or wait for a while
    wait_seconds = 0
    if (CLAIM_ONLY or full_health) and (utcnow > claim_reset_date):
        claimBonus(player_token)
        logger.info(pformat(game))
    elif not (CLAIM_ONLY or full_health) and (care_left > 0 or utcnow > care_reset_date):
        lowest_stat = min(current.items(), key=itemgetter(1))[0]
        giveCare(player_token, lowest_stat)
    elif CLAIM_ONLY or full_health:
        # wait until next action
        wait_seconds = 1
    else:
        # we hit the care limit; try again in about 6 minutes
        wait_seconds = (care_reset_date - utcnow).total_seconds()
        progress('Not yet! Remaining seconds: {}'.format(wait_seconds))
        
    return wait_seconds, claim_reset_date
    

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
    except (HTTPError, URLError) as e:
        logger.error('Claim Error: {}'.format(e))
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
        progress('{} -- Succesfully cared: {}'.format(game['score'], careType))
    except (HTTPError, URLError) as e:
        logger.error('Care Error: {}'.format(e))
    except:
        logger.exception('Unexpected Care Error:')

        
def progress(msg):
    logger.info(msg)
    
    
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
    
    
def get_next_dt(claim_reset_date=None):
    utcnow = datetime.datetime.utcnow()
    next_half_hour = ceil_dt(utcnow, datetime.timedelta(minutes=30))
    if next_half_hour.minute == 0:
        next_half_hour += datetime.timedelta(minutes=30)
    
    if claim_reset_date and utcnow < claim_reset_date < next_half_hour:
        return claim_reset_date
        
    return next_half_hour
        

if __name__ == '__main__':
    # one time next_dt init to 6 minutes ago
    next_dt = datetime.datetime.utcnow() - datetime.timedelta(minutes=6)

    while True:
        long_intervals = (lognormal(0, 2, size=10) + 1) * 2

        for liv in long_intervals:
            short_intervals = lognormal(0, 1, size=30) / 2
            
            game = getInfo(player_token)
            claim_reset = game['claim_reset_date']
            time.sleep(1 + short_intervals[-1])
            
            utcnow = datetime.datetime.utcnow()
            if bedtime <= utc_to_local(utcnow).hour < waketime:
                progress('ZzZzZzZ -- {} <= {} < {}'.format(bedtime, utc_to_local(utcnow).hour, waketime))
                next_dt = get_next_dt(claim_reset)
                seconds_until_claim = (claim_reset - utcnow).total_seconds()
                max_wait_seconds = 5 * 60
                
                if utcnow > claim_reset or seconds_until_claim <= max_wait_seconds:  
                    progress('Claim due {:%Y-%m-%d %H:%M:%S}'.format(utc_to_local(claim_reset)))
                else:
                    sleep_until(next_dt, random.random() * 4)
                
            wait = 0
            for siv in short_intervals:
                try:
                    wait, claim_reset = giveMostNeededCare(player_token)
                    if wait:
                        break
                except:
                    logger.exception('Unexpected issue:')
                    progress('Retrying in {} seconds'.format(wait + siv))
                    
                time.sleep(wait + siv)
            
            utcnow = datetime.datetime.utcnow()
            
            # keep trying until an action is taken or 9 minutes have passed
            if wait is 1 and (
                (last_action_time > next_dt)
                or (utcnow > next_dt + datetime.timedelta(minutes=9))
            ):
                next_dt = get_next_dt(claim_reset)
                sleep_until(next_dt, liv)
            else:
                snooze = wait + min(liv, 367.67)
                progress('Be back in {} seconds'.format(snooze))
                time.sleep(snooze)
                

