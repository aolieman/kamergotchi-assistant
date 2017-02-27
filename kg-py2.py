# Kamergotchi Automator
# https://github.com/MartienB/kamergotchi-automator
# Developed by: Martien Bonfrer
# Date: 20/2/17

from urllib import urlencode
from urllib2 import Request, urlopen, HTTPError, URLError
import time
import json
from urlparse import urljoin
import codecs
from random import randint
import datetime
import logging
from numpy.random import lognormal

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


def getInfo(player_token):
    url = 'https://api.kamergotchi.nl/game'
    headers = base_headers.copy()
    headers['x-player-token'] = player_token
    
    request = Request(url, headers=headers)

    # There is something wrong with the ssl certificate, so we just ignore it!
    try:
        json = urlopen(request).read().decode()
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

    foodValue = current['food']
    attentionValue = current['attention']
    knowledgeValue = current['knowledge']

    careReset = game['careReset']
    claimReset = game['claimReset']

    careResetDate = datetime.datetime.strptime(careReset, "%Y-%m-%dT%H:%M:%S.%fZ")
    claimResetDate = datetime.datetime.strptime(claimReset, "%Y-%m-%dT%H:%M:%S.%fZ")
    now = datetime.datetime.utcnow()

    # check if it is time to claim the bonus
    if (now > claimResetDate):
        claimBonus(player_token)

    # check if there are cares left, or if the careResetDate has elapsed (careLeft stays 0 even after reset date) .
    if (careLeft > 0 or now > careResetDate):

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
        return 0
    else:
        remainingSeconds = (careResetDate-now).total_seconds()
        progress('{}{}'.format('Not yet! Remaining seconds:', remainingSeconds))
        return remainingSeconds
    
    
def claimBonus(player_token):
    sessionUrl = 'https://api.kamergotchi.nl/game/claim'

    headers = base_headers.copy()
    headers['x-player-token'] = player_token

    req = Request(sessionUrl, headers=headers)
    req.get_method = lambda: 'POST'
    
    try: 
        response = urlopen(req)
        jsonresp = response.read().decode()
        
        progress('Succesfully claimed bonus!')
    except HTTPError as httperror:
        logger.exception('Claim Error:')
    except URLError as urlerror:
        logger.exception('Claim Error:')
    except:
        logger.exception('Unexpected Claim Error:')


def giveCare(player_token, careType):   
    sessionUrl = 'https://api.kamergotchi.nl/game/care'
    reqBody = {'bar' : careType}

    data = json.dumps(reqBody, separators=(',', ':')).encode('utf-8')

    headers = base_headers.copy()
    headers['x-player-token'] = player_token
    headers['Content-type'] = "application/json;charset=utf-8"

    req = Request(sessionUrl, data, headers)

    try: 
        response = urlopen(req)
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
    
    
def light_sleep(sec):
    remaining = sec
    while int(remaining) > 0:
        decr = min(5.0, remaining)
        print '.',
        time.sleep(decr)
        remaining -= decr
        
        # paranoid coding in the train
        if decr < 5:
            print('\n')
            break
        

if __name__ == '__main__':

    while True:
        now = datetime.datetime.now()
        if bedtime < now.hour < waketime:
            progress('ZzZzZzZ... for an hour and a bit')
            light_sleep(67 * 60)
        else:
            long_intervals = (lognormal(0, 2, size=10) + 1) * 2

            for liv in long_intervals:
                short_intervals = lognormal(0, 1, size=30) / 2
                
                for siv in short_intervals:
                    try:
                        wait = giveMostNeededCare(player_token)
                        if wait:
                            break
                    except (HTTPError, URLError):
                        logger.exception('Connection issue:')
                        progress('Retrying in {} seconds'.format(wait + siv))
                        
                    time.sleep(wait + siv)
                
                snooze = wait + min(liv, 37.7)
                progress('Be back in {} seconds'.format(snooze))
                light_sleep(snooze)
                

