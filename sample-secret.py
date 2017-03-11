from datetime import datetime, date, timezone, timedelta

PLAYER_ID = 'DEVICE_ID'

CET = timezone(timedelta(0, 3600), 'W. Europe Standard Time')
SLEEP_INTERVAL = (
    datetime(2017, 3, 10, 15, 20, tzinfo=CET), 
    datetime(2017, 3, 11, 0, 7, tzinfo=CET)
)


class Condition(object):
    def __init__(self, bool_condition):
        self.bool_condition = bool_condition
        
    def __bool__(self):
        return self.bool_condition()

        
def its_not_the_11th():
    return not date(2017, 3, 11) == datetime.now().date()


CLAIM_ONLY = Condition(its_not_the_11th)