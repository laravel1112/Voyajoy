import re

from BeautifulSoup import BeautifulSoup
from requests import get

from app.models.modeltuples import Photo, Location, Review, ScrapedListing

"""

Scrapes VRBO for the availability calendar
"""

BASE_URL_AIRBNB = "https://www.airbnb.com/rooms/"
BASE_URL_VRBO = "https://www.vrbo.com"

BODY_DATA_DICT = dict(
    CALENDAR_LAST_MODIFIED='data-calendarlastmodified',
    BEDROOMS='data-bedrooms',
    BATHROOMS='data-bathrooms',
    ACCOMODATES='data-sleeps',
    NUM_REVIEWS='data-totalreviews',
    AVG_REVIEWS='data-averagereviewrating',
    PROPERTY_TYPE='data-propertytype',
    AVG_PRICING='data-averagenightly',
    RATE_MAX='data-ratemaximum',
    RATE_MIN='date_rateminimum',
    PETS_ALLOWED='data-olbpetsallowed',
    UNIT_ID='data-unitid',
)

BODY_DATA_SET = set(BODY_DATA_DICT.values())


def clean_string(line):
    return " ".join(line.split())


def get_listing(vrbo_id):
    resp = get("%s/%s" % (BASE_URL_VRBO, vrbo_id))
    if resp.status_code != 200:
        print 'Problem with listing'
        return None
    html = resp.text
    s = BeautifulSoup(html)

    # get headline
    headline = clean_string([x[1] for x in s.find(attrs=dict(itemprop='name')).attrs if x[0] == 'content'][0])

    # get misc house info
    values = {x: '' for x in BODY_DATA_DICT.values()}
    body_attrs = s.find('body').attrs
    for attr in body_attrs:
        if attr[0] in BODY_DATA_SET:
            values[attr[0]] = attr[1]

    # get photos
    photos = list()
    photos_html = s.findAll('a', itemtype='http://schema.org/ImageObject')
    for p in photos_html:
        caption = p.find('meta', itemprop='caption').get('content')
        src = p.find('img').get('data-large')
        thumb = p.find('img').get('data-thumb')
        photos.append(Photo(caption=caption, src=src, thumb=thumb))

    # get lat lng
    m = re.search('zoom:([1-9]+),lat:([0-9\-\.]+),lng:([0-9\-\.]+),', html)
    location = Location(m.group(2), m.group(3), m.group(1))

    overview = clean_string(
        ''.join([str(item) for item in s.find('div', {'class': 'listing-desc'}).find('p').contents]))

    # get amenities
    amenities = dict()

    features = s.findAll('div', {'class': 'listing-features three'})
    for feature in features:
        category = feature.find('h3').contents[0].strip()
        spans = feature.findAll('span')
        keys = [x.contents[0] for x in spans]
        amenities[category] = keys

    reviews = get_reviews(vrbo_id, values['data-unitid'])
    if not reviews:
        reviews = list()
    listing = ScrapedListing(
        amenities=amenities,
        location=location,
        description=overview,
        photos=photos,
        headline=headline,
        bedrooms=float(values[BODY_DATA_DICT['BEDROOMS']]),
        bathrooms=float(values[BODY_DATA_DICT['BATHROOMS']]),
        sleeps=int(values[BODY_DATA_DICT['ACCOMODATES']]),
        avg_reviews=float(values[BODY_DATA_DICT['AVG_REVIEWS']]),
        num_reviews=int(values[BODY_DATA_DICT['NUM_REVIEWS']]),
        property_type=values[BODY_DATA_DICT['PROPERTY_TYPE']],
        pets_allowed=values[BODY_DATA_DICT['PETS_ALLOWED']],
        price=int(values[BODY_DATA_DICT['AVG_PRICING']].lstrip('$')),
        reviews=reviews
    )

    return listing


def get_reviews(vrbo_id, unit_id):
    url = 'https://www.vrbo.com/ListingPage.mvc/Reviews?systemId=vrbo&propertyId=%s&unitId=%s&isOwner=True&page=1' % (
        vrbo_id, unit_id)
    print url
    resp = get(url)
    if resp.status_code != 200:
        print 'Problem with listing', url
        return None
    s = BeautifulSoup(resp.text)
    allreviews = list()
    reviews = s.findAll('li', itemprop='review')
    for r in reviews:
        title = r.find('h3', {'class': 'propreview-title'}).contents[0]
        location_html = r.find('span', {'class': 'propreview-location'})
        location = location_html.contents[0] if location_html else None
        review_rating = r.find('meta', itemprop='ratingValue').get('content')
        body = r.find('div', itemprop='reviewBody').contents[0]
        stay_meta = r.find('ul', {'class': ' stay-meta'}).findAll('li')
        stayed = stay_meta[0].contents[-1]
        submitted = stay_meta[1].find('time').get('datetime')
        source = stay_meta[2].contents[-1]
        reviewer_name = r.find('span', itemprop='author').contents[0]
        reviewer_img = r.find("span", {"class": 'propreview-avatar'}).contents[0].get('src')
        reviewer_location = r.find("span", {"class": 'propreview-location'}).contents[0] if r.find("span", {
            "class": 'propreview-location'}) else None
        print '-------------------', reviewer_name, reviewer_img, reviewer_location
        allreviews.append(Review(
            location=str(location).strip(),
            title=str(title).strip(),
            rating=review_rating,
            body=str(body).strip(),
            date_stayed=str(stayed).strip(),
            datetime_submitted=submitted,
            source=str(source).strip(),
            reviewer_name=reviewer_name,
            reviewer_avatar=reviewer_img,
            reviewer_location=reviewer_location)
        )
    return allreviews


if __name__ == '__main__':
    import sys
    from pprint import pprint

    v = sys.argv[1]
    pprint(get_listing(v))
