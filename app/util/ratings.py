from BeautifulSoup import BeautifulSoup

from requests import get
from urlparse import urljoin as join

"""

Scrapes reviews from airbnb or vrbo
"""
BASE_URL_AIRBNB = "https://www.airbnb.com/rooms/"
BASE_URL_VRBO = "https://www.vrbo.com"


def get_ratings(airbnb_id=None, vrbo_id=None):
    ratings = dict()
    if airbnb_id:
        ratings['airbnb'] = _get_airbnb_ratings(airbnb_id)
    if vrbo_id:
        ratings['vrbo'] = _get_vrbo_ratings(vrbo_id)
    return ratings


def _get_airbnb_ratings(airbnb_id):
    try:
        url = join(BASE_URL_AIRBNB, airbnb_id)
        print url
        r = get(url)
        rating = None
        reviews = None
        if r.status_code == 200:
            s = BeautifulSoup(r.text)
            element = s.find(attrs=dict(itemprop='ratingValue'))
            for attr in element.attrs:
                if attr[0] == 'content':
                    rating = attr[1]
                    break
            element = s.find(attrs=dict(itemprop='reviewCount'))
            reviews = element.contents[0]
            return dict(rating=rating, reviews=reviews)
    except Exception, e:
        print 'error:', str(e)
    return None


def _get_vrbo_ratings(vrbo_id):
    try:
        url = join(BASE_URL_VRBO, vrbo_id)
        print url
        r = get(url)
        rating = None
        reviews = None
        if r.status_code == 200:
            s = BeautifulSoup(r.text)
            element = s.find(attrs=dict(itemprop='ratingValue'))
            for attr in element.attrs:
                if attr[0] == 'content':
                    rating = attr[1]
                    break
            element = s.find(attrs=dict(itemprop='reviewCount'))
            for attr in element.attrs:
                if attr[0] == 'content':
                    reviews = attr[1]
                    break
            return dict(rating=rating, reviews=reviews)
    except Exception, e:
        print 'error:', str(e)
    return None


if __name__ == '__main__':
    import sys

    a = sys.argv[1]
    v = sys.argv[2]
    print get_ratings(airbnb_id=a, vrbo_id=v)
