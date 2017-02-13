from pprint import pprint

from requests import get

from app.models.modeltuples import Photo, Location, Review, ScrapedListing

"""

Scrapes Airbnb for the availability calendar via apis
"""

BASE_URL_AIRBNB = "https://www.airbnb.com/rooms/"
AIRBNB_API_TEMPLATE = 'https://api.airbnb.com/v2/listings/%s?client_id=3092nxybyb0otqw18e8nh5nty&locale=en-US&currency=USD&_format=v1_legacy_for_p3&_source=mobile_p3'
AIRBNB_REVIEW_API_TEMPLATE = 'https://api.airbnb.com/v2/reviews?client_id=3092nxybyb0otqw18e8nh5nty&locale=en-US&currency=USD&_format=for_mobile_client&_000limit=20&_offset=0&_order=language&listing_id=%s&role=all'
AIRBNB_USER_API_TEMPLATE = 'https://api.airbnb.com/v2/users/%s?client_id=3092nxybyb0otqw18e8nh5nty&locale=en-US&currency=USD&_format=v1_legacy_show'


def clean_string(line):
    return " ".join(line.split())


def get_listing(airbnb_id):
    resp = get(AIRBNB_API_TEMPLATE % airbnb_id)
    pprint(resp.json())
    if resp.status_code != 200:
        print 'Problem with listing', resp.status_code
        return None
    j = resp.json()

    listing_json = j['listing']

    # get headline
    headline = listing_json['name']

    bathrooms = float(listing_json['bathrooms'])
    bedrooms = float(listing_json['bedrooms'])

    address = listing_json['address']
    beds = float(listing_json['beds'])

    cancelation_policy = listing_json['cancellation_policy']
    city = listing_json['city']
    state = listing_json['state']
    amenities = listing_json['amenities']
    print '===============', amenities
    country = listing_json['country']
    zipcode = str(listing_json['zipcode'])

    description = listing_json['description']

    max_guests = int(listing_json['person_capacity'])

    house_rules = listing_json['house_rules']

    interaction = listing_json['interaction']

    price_monthly = float(listing_json['listing_monthly_price_native']) if listing_json[
        'listing_monthly_price_native'] else None
    price_nightly = float(listing_json['price_native']) if listing_json['price_native'] else None
    price_security_deposit = float(listing_json['security_deposit_native']) if listing_json[
        'security_deposit_native'] else None

    price_extra_person = float(listing_json['listing_price_for_extra_person_native']) if listing_json[
        'listing_price_for_extra_person_native'] else None
    price_cleaning_fee = float(listing_json['listing_cleaning_fee_native']) if listing_json[
        'listing_cleaning_fee_native'] else None

    lat = float(listing_json['lat'])
    lng = float(listing_json['lng'])

    locale = listing_json['locale']

    min_nights = int(listing_json['min_nights'])
    notes = listing_json['notes']

    neighborhood_overview = listing_json['neighborhood_overview']
    neighborhood = listing_json['neighborhood']  # not sure what this is

    photos_json = listing_json['photos']
    # caption, large, thumbnail, large_cover?

    property_type = listing_json['property_type']

    recent_review = listing_json['recent_review']

    space = listing_json['space']

    rating = float(listing_json['star_rating']) if listing_json['star_rating'] else 0
    review_count = int(listing_json['reviews_count'])

    summary = listing_json['summary']

    transit_info = listing_json['transit']

    reviews = list()
    review_response = get(AIRBNB_REVIEW_API_TEMPLATE % airbnb_id)
    if review_response.status_code != 200:
        print 'something is wrong with review fetching', review_response.status_code
    else:
        review_json = review_response.json()
        reviews_json = review_json['reviews']
        review_count = int(review_json['metadata']['reviews_count'])
        for each in reviews_json:
            body = each['comments']
            created_at = each['created_at']
            author = each['author']
            author_id = author['id']
            author_first_name = author['first_name']
            author_avatar = author['picture_url']
            user_response = get(AIRBNB_USER_API_TEMPLATE % author_id)
            author_location = None
            if user_response.status_code == 200:
                user_json = user_response.json()
                author_location = user_json['user']['location']
                author_first_name = user_json['user']['first_name']
                author_avatar = user_json['user']['picture_url']
            reviews.append(Review(
                location=listing_json['smart_location'],
                title=None,
                body=body,
                datetime_submitted=created_at,  # 2016-01-25T14:26:26Z
                source='Airbnb',
                rating=None,
                date_stayed=None,
                reviewer_name=author_first_name,
                reviewer_location=author_location,
                reviewer_avatar=author_avatar
            ))

    photos = list()
    for p in photos_json:
        photos.append(Photo(
            caption=p['caption'],
            src=p['large'],
            thumb=p['thumbnail']
        ))

    map_image_url = listing_json['map_image_url']
    import re
    m = re.search('zoom=([0-9]+)', map_image_url)

    location = Location(
        zoom=m.group(1),
        lat=lat,
        lng=lng
    )

    listing = ScrapedListing(
        amenities=amenities,
        location=location,
        description=description,
        photos=photos,
        headline=headline,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        sleeps=max_guests,
        avg_reviews=rating,
        num_reviews=review_count,
        property_type=property_type,
        pets_allowed=None,
        price=price_nightly,
        reviews=reviews,
        security_deposit=price_security_deposit,
        cleaning_fee=price_cleaning_fee,
        price_monthly=price_monthly,
        price_extra_person=price_extra_person,
        summary=summary,
        neighborhood=neighborhood_overview,
        city=city,
        state=state,
        zipcode=zipcode,
        country=country,
        space=space,
        transit_info=transit_info,
        min_nights=min_nights,
        house_rules=house_rules,
        notes=notes,
        locale=locale,
        guest_interaction=interaction,
        address=address
    )

    return listing


if __name__ == '__main__':
    import sys

    v = sys.argv[1]
    get_listing(v)
