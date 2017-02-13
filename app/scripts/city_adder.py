from parse_rest.connection import register

from app.models.parse import Listing, City

register('EVIR76KVNxQ4IFoNvudoLg2a4wPWaCnnKSjkuhkq', 'o7WTfdYVrCvT8AOTqZRPxnnfMZx1AAKUmaW3yaAX')
listings = Listing.Query.all().select_related('placeDetails', 'photos')

import os

os.system('say "starting"')
for x, each in enumerate(listings):
    try:
        place = each.placeDetails
        city = place.city
        if city:
            print city
            os.system('say %s' % city)
            try:
                c = City.Query.get(city=city)
                print 'city exists'
            except:
                c = City(city=city, image=each.photos[0].large)
                c.save()
            each.city = c
            each.save()
    except Exception, e:
        print str(e)
        os.system('error')

os.system('say "finished"')