from datetime import datetime

from parse_rest.datatypes import Date

from app import flaskapp


def get_datetime(date_string):
    date_format = '%m/%d/%Y'
    date = datetime.strptime(date_string, date_format)
    return date;


def get_date_delta_days(start, end):
    delta = (end - start).days
    return delta


def get_friendly_from_parse_date(date, short_month=False):
    friendly_format = '%B %d, %Y' if not short_month else '%b %d, %Y'

    if isinstance(date, Date):
        date_format = '%Y-%m-%d %H:%M:%S'
        d = datetime.strptime(str(date._date), date_format)
    elif isinstance(date, dict):
        if 'iso' in date:#2016-02-11T05:20:28.954Z'
            date_str = date['iso']
            date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
            d = datetime.strptime(date_str, date_format)
            friendly_format = '%B %Y'

    else:
        d = date
    return d.strftime(friendly_format)

flaskapp.jinja_env.globals['get_friendly_date'] = get_friendly_from_parse_date