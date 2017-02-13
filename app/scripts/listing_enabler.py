from parse_rest.connection import register

from app.models.parse import Listing

register('EVIR76KVNxQ4IFoNvudoLg2a4wPWaCnnKSjkuhkq', 'o7WTfdYVrCvT8AOTqZRPxnnfMZx1AAKUmaW3yaAX')
listings = Listing.Query.all()

import os

os.system('say "starting"')
for x, each in enumerate(listings):
    try:
        print each
        if hasattr(each, 'disabled'):
            continue
        each.disabled = False
        each.save()
    except Exception, e:
        print str(e)
        os.system('error')

os.system('say "finished"')