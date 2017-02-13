from parse_rest.connection import register
from parse_rest.user import User

from app.calendar import vrbo_scraper
from app.models.parse import ListingUrlMapping, Listing

register('EVIR76KVNxQ4IFoNvudoLg2a4wPWaCnnKSjkuhkq', 'o7WTfdYVrCvT8AOTqZRPxnnfMZx1AAKUmaW3yaAX')
maps = ListingUrlMapping.Query.all().select_related("listing")
listings = Listing.Query.filter(src="Vrbo").select_related("creator", "placeDetails")

for each in listings:
    try:
        print each.creator.fullName
        m = ListingUrlMapping.Query.get(listing=each)
        vrbo_url = m.id_vrbo

        s = vrbo_scraper.get_listing(vrbo_url)
        each.overview = s.description
        each.creator = User.Query.get(objectId=each.creator.objectId)
        each.save()
    except Exception, e:
        print 'error', str(e)