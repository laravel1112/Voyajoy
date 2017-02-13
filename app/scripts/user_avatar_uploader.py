from BeautifulSoup import BeautifulSoup
from parse_rest.connection import register
from parse_rest.user import User
from requests import get

from app.models.parse import ListingUrlMapping, Listing

register('EVIR76KVNxQ4IFoNvudoLg2a4wPWaCnnKSjkuhkq', 'o7WTfdYVrCvT8AOTqZRPxnnfMZx1AAKUmaW3yaAX', master_key='wKCk6XV5cXspJUmJfxjBDsjm1R7ZLZlKgksUUaWC')
listings = Listing.Query.all().select_related("creator")

users = set()

AIRBNB_API_TEMPLATE = 'https://api.airbnb.com/v2/listings/%s?client_id=3092nxybyb0otqw18e8nh5nty&locale=en-US&currency=USD&_format=v1_legacy_for_p3&_source=mobile_p3'
AIRBNB_REVIEW_API_TEMPLATE = 'https://api.airbnb.com/v2/reviews?client_id=3092nxybyb0otqw18e8nh5nty&locale=en-US&currency=USD&_format=for_mobile_client&_000limit=20&_offset=0&_order=language&listing_id=%s&role=all'
AIRBNB_USER_API_TEMPLATE = 'https://api.airbnb.com/v2/users/%s?client_id=3092nxybyb0otqw18e8nh5nty&locale=en-US&currency=USD&_format=v1_legacy_show'


for l in listings:
    print l
    user = l.creator
    if user.objectId in users:
        continue
    users.add(user.objectId)
    mapping = ListingUrlMapping.Query.get(listing=l)
    print mapping
    airbnb_id = mapping.id_airbnb if hasattr(mapping, 'id_airbnb') and mapping.id_airbnb != '' else None
    vrbo_id = mapping.id_vrbo if hasattr(mapping, 'id_vrbo') and mapping.id_vrbo != '' else None
    print airbnb_id, vrbo_id
    if airbnb_id:
        url = AIRBNB_API_TEMPLATE % airbnb_id
        print url
        r = get(url)
        print r.status_code
        if r.status_code == 200:
            j = r.json()
            u = User.login(user.username, 'pleasechangeme')
            user_avatar = j['listing']['user']['user']['picture_url']
            u.avatar = user_avatar
            u.save()
        else:
            continue
    elif vrbo_id:
        url = 'https://www.vrbo.com/%s' % vrbo_id
        r = get(url)
        if r.status_code == 200:
            b = BeautifulSoup(r.text)
            element = b.find('span', {'class': 'contactwidget-photo-inner'})
            if element:
                u = User.login(user.username, 'pleasechangeme')
                avatar = element.contents[0].get('src')
                if avatar:
                    u.avatar = avatar
                    u.save()





