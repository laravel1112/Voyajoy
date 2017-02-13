from datetime import datetime, timedelta

from requests import get
from urlparse import urljoin as join
from urllib import urlencode
from time import strptime

"""

Communicates with the scraper companion class to obtain the availability calendar
"""

URL_BASE_API = 'https://www.airbnb.com/api/v2/'
METHOD_CALENDAR = 'calendar_months'
URL_API_CALENDAR = join(URL_BASE_API, METHOD_CALENDAR)
KEY_API_AIRBNB = 'd306zoyjsyarp7ifhu67rjxn52tv0t20'
URL_AIRBNB_CALENDAR = 'https://www.airbnb.com/api/v2/calendar_months?key=d306zoyjsyarp7ifhu67rjxn52tv0t20&currency=USD&locale=en&listing_id=5069867&month=1&year=2016&count=3&_format=with_conditions'
URL_UNAVAILABLE_CALENDAR = 'https://api.airbnb.com/v2/calendar_days?client_id=3092nxybyb0otqw18e8nh5nty&locale=en-US&currency=USD&_format=with_conditions&listing_id=%s&start_date=%s&end_date=%s'

URL_API_CALENDAR_PRICING = 'https://api.airbnb.com/v2/calendar_days'


def get_pricing(start_date, end_date, listing_id, num_guests):
    params = [
        ('client_id', '3092nxybyb0otqw18e8nh5nty'),
        ('start_date', start_date),
        ('end_date', end_date),
        ('listing_id', listing_id),
        ('currency', 'USD'),
        ('_format', 'with_conditions'),
        ('locale', 'en-US')
    ]

    r = get(URL_API_CALENDAR_PRICING, params=params)
    print r.url
    print r.status_code
    if r.status_code == 200:
        j = r.json()
        return j['calendar_days']
    return list()


def _get_calendar_args(listing_id, month, year):
    return dict(
        key=KEY_API_AIRBNB,
        locale='en',
        listing_id=listing_id,
        month=month,
        year=year,
        count=3,
    )


# TODO should get this from client
def get_calendar(listing_id, start_date):
    print 'get calendar listing'
    end_date = start_date + timedelta(365)
    url = URL_UNAVAILABLE_CALENDAR % (listing_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    print url
    print 'created airbnb url'
    response = get(url)
    if response.status_code == 200:
        calendar_json = response.json()
        result = _from_json(calendar_json)
        print result
        return result
    else:
        return dict(error=response.status_code)


def _from_json(json):
    availability_calendar = list()
    for d in json['calendar_days']:
        if not d['available']:
            date = d['date']
            dtime = datetime.strptime(date, '%Y-%m-%d')
            availability_calendar.append(dtime.strftime('%m/%d/%Y'))
    return availability_calendar


def __from_json(json):
    months = json['calendar_months']
    availability_calendar = list()
    for m in months:
        x = iter(m['days'])
        d = x.next()
        start = d['date']
        end = start
        print availability_calendar, start, end
        a = d['available']
        try:
            while True:
                start = d['date']
                a = d['available']
                # print a, d['available']
                while d['available'] is a:
                    d = x.next()
                    end = d['date']
                    # print start, end
                availability_calendar.append(dict(start=start, end=end, available=a))
        except StopIteration:
            availability_calendar.append(dict(start=start, end=end, available=a))
    return availability_calendar
