import re
from datetime import datetime

from parse_rest.connection import register
from parse_rest.datatypes import Date
from parse_rest.user import User

from app.calendar import vrbo_scraper
from app.models.parse import ListingUrlMapping, Listing, Review
from app.util import airbnb_scraper
from app.util import imageuploader

register('EVIR76KVNxQ4IFoNvudoLg2a4wPWaCnnKSjkuhkq', 'o7WTfdYVrCvT8AOTqZRPxnnfMZx1AAKUmaW3yaAX')
listings = Listing.Query.all().select_related("creator")
listings = Listing.Query.all().filter(objectId='0ydsO0PRYQ').select_related("creator")
import os

os.system('say "starting"')
for x, each in enumerate(listings):
    print "listing #%s" % x
    print each.headline, each.creator.fullName
    try:
        m = ListingUrlMapping.Query.get(listing=each)

        if each.src == 'Vrbo':
            s = vrbo_scraper.get_listing(m.id_vrbo)
        else:
            s = airbnb_scraper.get_listing(m.id_airbnb)

        reviews = s.reviews
        review_list = list()
        for r in reviews:
            avatar = imageuploader.upload_image(r.reviewer_avatar)
            print avatar
            date = None
            if each.src == 'Vrbo':
                date = Date(datetime.strptime(r.datetime_submitted, '%Y-%m-%d'))
            else:
                m = re.search('([0-9]+-[0-9]+-[0-9]+)T', r.datetime_submitted)
                if m:
                    asdf = m.group(1)
                    date = Date(datetime.strptime(asdf, '%Y-%m-%d'))
            review = Review(
                    title=r.title,
                    body=r.body,
                    rating=r.rating,
                    location=r.location,
                    date_stayed=r.date_stayed,
                    datetime_submitted=date,
                    source=r.source,
                    reviewer_name=r.reviewer_name,
                    reviewer_avatar=avatar,
                    reviewer_location=r.reviewer_location
                )
            print review.save()
            review_list.append(review)
        print review_list
        each.reviews = review_list
        each.creator = User.Query.get(objectId=each.creator.objectId)
        print each.save()
    except Exception, e:
        os.system('say "error"')
        print 'error', str(e)

os.system('say "finished"')