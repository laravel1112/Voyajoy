import app.util.ratings
from app.models.parse import ListingUrlMapping


def upload_ratings():
    mappings = ListingUrlMapping.Query.all()

    for l in mappings:
        r = app.util.ratings.get_ratings(l.id_airbnb, l.id_vrbo)
        value = 0
        count = 0
        for each in r:
            c = r[each]['reviewCount']
            rat = r[each]['reviewRating']
            value += rat * c
            count += c
        rating = value/count
        print value, count
        listing = app.util.ratings.listing
        listing.reviewCount = count
        listing.reviewRating = rating
        print listing
        break
        listing.save()

if __name__ == '__main__':
    print __package__
    from parse_rest.connection import register
    register('EVIR76KVNxQ4IFoNvudoLg2a4wPWaCnnKSjkuhkq', 'o7WTfdYVrCvT8AOTqZRPxnnfMZx1AAKUmaW3yaAX', master_key='wKCk6XV5cXspJUmJfxjBDsjm1R7ZLZlKgksUUaWC')
    upload_ratings()