from collections import namedtuple

Review = namedtuple('Review', 'reviewer_location reviewer_name reviewer_avatar location title body rating date_stayed datetime_submitted source')
Photo = namedtuple('photo', 'caption src thumb')
Location = namedtuple('Location', 'lat lng zoom')
ScrapedListing = namedtuple('ScrapedListing', 'address guest_interaction locale notes house_rules min_nights transit_info space country zipcode state city neighborhood summary price_extra_person price_monthly cleaning_fee security_deposit bedrooms bathrooms sleeps avg_reviews num_reviews property_type price pets_allowed headline photos location description amenities reviews')
ScrapedListing.__new__.__defaults__ = (None,) * len(ScrapedListing._fields)
TuplePlace = namedtuple('TuplePlace', 'street city state zipcode country')
