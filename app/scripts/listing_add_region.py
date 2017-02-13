from parse_rest.connection import register

from app.models.parse import Listing

register('EVIR76KVNxQ4IFoNvudoLg2a4wPWaCnnKSjkuhkq', 'o7WTfdYVrCvT8AOTqZRPxnnfMZx1AAKUmaW3yaAX')
listings = Listing.Query.all().select_related("city", "city.region", 'region')

import os

os.system('say "starting"')
for x, each in enumerate(listings):
    try:
        if hasattr(each, 'region'):
            print 'skipping', each
            continue
        city = each.city
        region = city.region
        print region
        each.region = region
        each.save()
    except Exception, e:
        print str(e)
        os.system('error')

os.system('say "finished"')