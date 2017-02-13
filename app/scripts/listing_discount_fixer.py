from parse_rest.connection import register

from app.models.parse import Listing

register('EVIR76KVNxQ4IFoNvudoLg2a4wPWaCnnKSjkuhkq', 'o7WTfdYVrCvT8AOTqZRPxnnfMZx1AAKUmaW3yaAX')
listings = Listing.Query.all()

import os

os.system('say "starting"')
for x, each in enumerate(listings):
    each.discountedRate = 15
    each.save()

os.system('say "finished"')