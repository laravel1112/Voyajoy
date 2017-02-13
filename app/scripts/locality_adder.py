from parse_rest.connection import register

from app.models.parse import City, Region

register('EVIR76KVNxQ4IFoNvudoLg2a4wPWaCnnKSjkuhkq', 'o7WTfdYVrCvT8AOTqZRPxnnfMZx1AAKUmaW3yaAX')
listings = City.Query.all()

import os

os.system('say "starting"')
for x, each in enumerate(listings):
    try:
        locality = each.locality
        if locality:
            print locality
            os.system('say %s' % locality)
            try:
                c = Region.Query.get(name=locality)
                print 'city exists'
            except:
                c = Region(name=locality, image=each.image)
                c.save()
            each.region = c
            each.save()
    except Exception, e:
        print str(e)
        os.system('error')

os.system('say "finished"')