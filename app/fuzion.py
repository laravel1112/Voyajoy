import json
import re
from datetime import datetime

from requests import get

from app.models.parse import ListingUrlMapping, Listing

"""

This file contains methods that checks airbnb and vrbo for availabilities.
Airbnb currently uses a reverse engineered api to obtain calendar information
VRBO scrapes data from their webpage
"""


def get_availability(start_date, end_date, post_id, num_guests=1):
    print start_date, end_date, num_guests
    available = True
    found = False
    check_results = dict()
    for name, func in CHECKS.iteritems():
        print name, func
        if not ID_CHECKS[name](post_id):
            print 'cant find'
            continue
        found = True
        print func
        resp = func(start_date, end_date, post_id, num_guests)
        print 'resp', resp
        if name == 'siteAirbnb' and not resp['available']:  # todo bad assumption to make?
            available = False
        check_results[name] = available
    return dict(
        checkInDate=start_date,
        checkOutDate=end_date,
        available=available if found else True,
        numOfGuests=num_guests,
        **check_results
    )


def get_vrbo_availablility(start_date, end_date, post_id, num_guests=1):
    print 'checking vrbo for availability'
    vrbo_id = _get_vrbo_id(post_id)
    resp = _get_vrbo_dates(vrbo_id, start_date, end_date, num_guests)
    return dict(
        checkInDate=start_date,
        checkOutDate=end_date,
        available=resp,
        numOfGuests=num_guests
    )


def get_airbnb_availablility(start_date, end_date, post_id, num_guests=1):
    print 'checking airbnb for availability'
    airbnb_id = _get_airbnb_id(post_id)
    print 'airbnb_id', airbnb_id
    resp = _get_airbnb_dates(airbnb_id, start_date, end_date, num_guests)
    print 'resp', resp
    return dict(
        checkInDate=start_date,
        checkOutDate=end_date,
        available=resp,
        numOfGuests=num_guests
    )


def _get_vrbo_id(post_id):
    try:
        listing = Listing(objectId=post_id)
        mapping = ListingUrlMapping.Query.get(listing=listing)
        return mapping.id_vrbo
    except Exception, e:
        print 'error', str(e)
        return None


def _get_airbnb_id(post_id):
    try:
        listing = Listing(objectId=post_id)
        print 'listing', listing
        mapping = ListingUrlMapping.Query.get(listing=listing)
        print 'mapping', mapping
        return mapping.id_airbnb
    except Exception, e:
        print 'error', str(e)
        return None


def _get_airbnb_dates(airbnb_id, start_date, end_date, num_of_guests):
    try:
        start_datetime = datetime.strptime(start_date, '%m/%d/%Y')
        end_datetime = datetime.strptime(end_date, '%m/%d/%Y')
        delta = end_datetime - start_datetime
        nights = delta.days
        params = [
            ('client_id', '3092nxybyb0otqw18e8nh5nty'),
            ('checkin', start_datetime.strftime('%Y-%m-%d')),
            ('guests', num_of_guests),
            ('listing_id', airbnb_id),
            ('nights', nights)
        ]
        url = 'https://api.airbnb.com/v2/pricing_quotes'
        r = get(url, params=params)
        print 'status_code', r.status_code, r.url
        if r.status_code != 200:
            return True
        import pprint
        pprint.pprint(vars(r))
        print r.status_code
        status = r.json()['pricing_quotes'][0]['availability_status']
        return status == 0 or status == 2
    except Exception, e:
        print 'error', str(e)
        return True


def _get_vrbo_dates(vrbo_id, start_date, end_date, num_of_guests):
    try:
        date_format = '%m/%d/%Y'
        vrbo_url = 'https://www.vrbo.com/%s' % vrbo_id
        r = get(vrbo_url)
        print r.status_code
        if r.status_code == 200:
            m = re.search('VRBO.unitAvailability = ({.+})', r.text)
        o = json.loads(m.group(1))
        date_range = o['dateRange']
        date_start = date_range['beginDate']
        datetime_start = datetime.strptime(date_start, date_format)
        check_in_date = datetime.strptime(start_date, date_format)
        check_out_date = datetime.strptime(end_date, date_format)

        delta = (check_in_date - datetime_start).days

        check_range_delta = (check_out_date - check_in_date).days
        availability_str = o['unitAvailabilityConfiguration']['availability']
        for x in range(delta, delta + check_range_delta):
            if availability_str[x] == 'N':
                return False
        return True
    except:
        return False


CHECKS = dict(
    siteVrbo=get_vrbo_availablility,
    siteAirbnb=get_airbnb_availablility
)

ID_CHECKS = dict(
    siteVrbo=_get_vrbo_id,
    siteAirbnb=_get_airbnb_id
)
