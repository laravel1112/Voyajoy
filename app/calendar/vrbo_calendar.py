import re

from datetime import datetime, timedelta
from flask import json
from requests import get
from urlparse import urljoin as join

"""

Communicates with the scraper companion class to obtain the availability calendar
"""

BASE_URL = 'https://www.vrbo.com'


def _do_get(vrbo_id):
    response = get(join(BASE_URL, vrbo_id))

    print response.status_code
    if response.status_code == 200:
        m = re.search('VRBO.unitAvailability = ({.+})', response.text)
        o = json.loads(m.group(1))
        return o
    raise Exception()


def get_calendar(vrbo_id, month=None, year=None):
    try:
        date_format = '%m/%d/%Y'
        o = _do_get(vrbo_id)

        date_range = o['dateRange']
        date_start = date_range['beginDate']
        datetime_start = datetime.strptime(date_start, date_format)
        check_in_date = datetime_start
        check_out_date = datetime_start + timedelta(12*365/12)
        print check_in_date, check_out_date
        delta = (check_out_date - check_in_date).days

        availability_calendar = list()
        availability_str = o['unitAvailabilityConfiguration']['availability']

        for x in range(0, delta):
            day = check_in_date + timedelta(days=x)
            if availability_str[x] == 'N':
                availability_calendar.append(day.strftime('%m/%d/%Y'))
        return availability_calendar
    except Exception, e:
        print 'error', str(e)
        return None
