import json
import os
import re
from datetime import datetime
from functools import wraps
from random import sample
from urlparse import urlparse, urljoin

from flask import request, render_template, url_for, make_response, jsonify, session, g
from parse_rest.connection import SessionToken, MasterKey
from parse_rest.datatypes import GeoPoint, Date
from parse_rest.user import User, login_required
from premailer import transform
from werkzeug.utils import redirect

from app import flaskapp, payment
from app import mailer
from app.calendar import vrbo_scraper
from app.models.modeltuples import TuplePlace
from app.models.parse import Listing, Place, Review, Photo, ListingUrlMapping, Reservation, Billing, Verification, \
    Region, PasswordResetRequest
from app.util import imageuploader
from app.calendar import airbnb_scraper


def validate_fields(fields):
    for each in fields:
        if each not in request.form:
            return False


def get_random_listings(n):
    random_listings = list()
    try:
        listings = Listing.Query.all().select_related("photos").filter(disabled=False)
        random_sample = sample(range(1, len(listings)), n)
        print random_sample
        random_listings = [listings[x] for x in random_sample]
        print random_listings
    except Exception, e:
        print 'ivan', str(e)
    return random_listings


@flaskapp.route('/blah')
def get_listings_sort_by_locality():
    try:
        listings = Listing.Query.all().select_related('photos', 'placeDetails').filter(disabled=False)
        listings_collated = dict()
        for l in listings:
            city = l.placeDetails.city
            if city not in listings_collated:
                listings_collated[city] = list()
            listings_collated[city].append(l)
        from pprint import pprint
        pprint(listings_collated)

        return jsonify([(x, len(listings_collated[x])) for x in listings_collated])
    except Exception, e:
        print 'ivan', str(e)
    return 'bleh'


@flaskapp.route("/rentals")
@flaskapp.route('/')
def index():
    listings = get_random_listings(6)
    # listings=list()
    cities = Region.Query.all().order_by("name").order_by("-weight")
    return render_template('main.html', featured_listings=listings, cities=cities)


def get_redirect_target():
    if request.values:
        print 'next target', request.values.get('next')
    print request.args
    for target in request.values.get('next') if request.values else []:
        if not target:
            continue
        if is_safe_url(target):
            return target


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def redirect_back(default_target, **values):
    target = request.form['next'] if 'next' in request.form else None
    print 'target', target
    if not target and 'next' in request.args:
        target = request.query_string
    if 'redirect_booking_target' in session:
        target = session['redirect_booking_target']
        session.pop('redirect_booking_target')
        if is_safe_url(target):
            return redirect(target)
    if not target or not is_safe_url(target):
        target = url_for(default_target, **values)
    return redirect(target)

def get_target_redirect_back(default_target, **values):
    target = request.form['next'] if 'next' in request.form else None
    print 'target', target
    if not target and 'next' in request.args:
        target = request.query_string
    if not target or not is_safe_url(target):
        target = url_for(default_target, **values)
    return target


@flaskapp.route("/loginAjax", methods=['POST'])
def login_ajax():
    email = request.form['email']
    pw = request.form['password']
    try:
        user = User.login(email.lower(), pw)
        session['session_id'] = user.sessionToken
        redirect_to = 'dashboard'
        target = get_target_redirect_back(redirect_to)
        return jsonify(dict(success=True, session=user.sessionToken, target=target))
    except Exception, e:
        return jsonify(dict(success=False, message=e.message))


@flaskapp.route("/signupAjax", methods=['POST'])
def signup_ajax():
    fields = ['email', 'password', 'firstname', 'lastname']
    if validate_fields(fields):
        return jsonify(dict(success=False, message='missing fields'))
    email = request.form['email']
    pw = request.form['password']
    first = request.form['firstname']
    last = request.form['lastname']
    next = request.form['next'] if 'next' in request.form else None
    try:
        user = User.signup(email.lower(), pw, firstName=first, lastName=last, email=email, fullName='%s %s' % (first, last))
        v = Verification(user=user)
        v.save()
        logged_in_user = User.login(email.lower(), pw)
        session['session_id'] = logged_in_user.sessionToken
        mailer.send_user_verification_mail(email, first, v.objectId, next=next)
        return jsonify(dict(success=True, session=logged_in_user.sessionToken, target=url_for('signup_success')))
    except Exception, e:
        return jsonify(dict(success=False, message=e.message))


@flaskapp.route("/signup_success")
def signup_success():
    return render_template('/account/sign_up_successful.html')


@flaskapp.route("/login", methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('dashboard'))
    error = None
    error_message = None
    if request.method == 'POST':
        email = request.form['email']
        pw = request.form['password']
        try:
            user = User.login(email.lower(), pw)
            session['session_id'] = user.sessionToken
            if user.is_authenticated():
                redirect_to = "dashboard"
                # r = Reservation.Query.filter(renter=user)
                # if not r:
                #     redirect_to = "index"
                resp = make_response(redirect_back(redirect_to))
                return resp
        except Exception, e:
            print str(e)
            error = json.loads(str(e))
    if error and error['code'] == 101:
        error_message = 'The email/password entered is incorrect'

    return render_template(
        'account/sign_in.html',
        error=error_message if error_message else None
    )


@flaskapp.route("/signup", methods=['GET', 'POST'])
def sign_up():
    next = request.form['next'] if 'next' in request.form else None
    if request.method == 'GET':
        if g.user:
            return redirect(url_for('dashboard'))
        return render_template('account/sign_up.html')
    else:
        fields = ['email', 'password', 'firstname', 'lastname']
        if validate_fields(fields):
            return render_template('account/sign_up.html', error="missing fields")
        email = request.form['email']
        pw = request.form['password']
        first = request.form['firstname']
        last = request.form['lastname']
        try:
            user = User.signup(email.lower(), pw, firstName=first, lastName=last, email=email, fullName='%s %s' % (first, last))
            v = Verification(user=user)
            v.save()
            logged_in_user = User.login(email.lower(), pw)
            session['session_id'] = logged_in_user.sessionToken
            g.user = logged_in_user
            mailer.send_user_verification_mail(email, first, v.objectId, next=next)
            return render_template('/account/sign_up_successful.html')
        except Exception, e:
            error = str(e)
    return render_template('account/sign_up.html', next=next, error=error)


@flaskapp.route("/sign_up_successful")
def sign_up_successful():
    return render_template('/account/sign_up_successful.html')


def get_rentals():
    return "todo"


AIRBNB_API_URL = 'https://api.airbnb.com/v2/listings/%s?client_id=3092nxybyb0otqw18e8nh5nty&locale=en-US&currency=USD&_format=v1_legacy_for_p3&_source=mobile_p3'


def _get_photos_from_airbnb(listing):
    try:
        m = ListingUrlMapping.Query.get(listing=listing)
        if not m.id_airbnb:
            return None
        from requests import get
        url = AIRBNB_API_URL % m.id_airbnb
        r = get(url)
        j = r.json()
        photos = j['listing']['xl_picture_urls']
        thumbs = j['listing']['thumbnail_urls']
        return [Photo(thumb=x[1],large=x[0]) for x in zip(photos,thumbs)]
    except:
        return None


@flaskapp.route("/browse/<region_id>")
def browse(region_id):
    try:
        r = Region.Query.get(objectId=region_id)
        listings = Listing.Query.all().filter(region=r, disabled=False).select_related('photos')
        return render_template("browse.html", listings=listings, region=r)
    except Exception, e:
        print str(e)
        return '', 404


@flaskapp.route("/rentals/<listing_id>")
def get_rental(listing_id):
    try:
        args = dict()
        user = g.user
        listing_query = Listing.Query.all().filter(objectId=listing_id).select_related("photos", "reviews")
        if listing_query:
            listing = listing_query[0]
            print listing

        airbnb_photos = _get_photos_from_airbnb(listing)
        if airbnb_photos:
            listing.photos = airbnb_photos
        if user:
            try:
                existing_reservation = Reservation.Query.filter(renter=user, listing=listing)
                if existing_reservation:
                    args['reservation'] = existing_reservation[0]
            except Exception, e:
                print 'error, no reservation exists', str(e)
        args['listing'] = listing
        args['place'] = listing.placeDetails
        thumbs = list()
        photos = list()
        for x in listing.photos:
            thumbs.append(x.thumb.strip())
            photos.append(x.large.strip())
        args['thumbnails'] = thumbs
        listing.photos = photos
        listing.houseRulesText = listing.houseRulesText.replace('\n', '<br /r>') if hasattr(listing, 'houseRulesText') else None
        listing.placeText = listing.placeText.replace('\n', '<br />') if hasattr(listing, 'placeText') else None
        listing.neighborhoodText = listing.neighborhoodText.replace('\n', '<br />') if hasattr(listing, 'neighborhoodText') else None
        listing.overviewText = listing.overviewText.replace('\n', '<br />') if hasattr(listing, 'overviewText') else None
        listing.gettingAroundText = listing.gettingAroundText.replace('\n', '<br />') if hasattr(listing, 'gettingAroundText') else None
        listing.moreDetailsText = listing.moreDetailsText.replace('\n', '<br />') if hasattr(listing, 'moreDetailsText') else None
        return render_template('listing.html', **args)
    except Exception, e:
        return '', 404


@flaskapp.route("/logout")
def logout():
    if not g.user:
        return make_response(redirect(url_for('login')))
    resp = make_response(redirect(url_for('login')))
    session.pop('session_id')
    if 'redirect_booking_target' in session:
        session.pop('redirect_booking_target')
    g.user = None
    return resp


@flaskapp.route("/verify")
def verify():
    try:
        token = request.args.get("t", None)
        next = request.args.get("next", None)
        if not token:
            return render_template('account/verification_invalid.html')
        v = Verification.Query.get(objectId=token)
        v.verified = True
        v.save()
        print "verification successful: ", v
        return render_template('account/email_verification.html', next=next)
    except Exception, e:
        return render_template('account/verification_invalid.html')


@flaskapp.route('/test_mail')
@login_required
def test_mail():
    print g.user.objectId
    mailer.send_user_verification_mail(g.user)
    return 'done', g.user.currentToken


@flaskapp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form["email"]
        try:
            user = User.Query.get(email=email)
        except Exception, e:
            return render_template('account/password_request_sent.html')
        try:
            reset_requests = PasswordResetRequest.Query.all().filter(user=user)
            for each in reset_requests:
                each.delete()
        except Exception, e:
            print str(e)
        p = PasswordResetRequest(user=user)
        p.save()
        mailer.send_password_reset_request(email, user.firstName, p.objectId)
        return render_template('account/password_request_sent.html')
    return render_template('account/forgot_password.html')


@flaskapp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        token = request.form.get('t', None)
        password = request.form.get('password')
        print token, password
        try:
            password_request = PasswordResetRequest.Query.get(objectId=token)
            user = password_request.user
            with MasterKey(flaskapp.config['PARSE_MASTER_KEY']):
                user.password = password
                user.sessionToken = None
                user.save()
                password_request.delete()
            return render_template('auth/password_updated.html')
        except Exception, e:
            print str(e)
            return '', 404 #waahha

    token = request.args.get('t', None)
    if not token:
        return render_template('auth/password_reset_request_expired.html')
    try:
        password_request = PasswordResetRequest.Query.get(objectId=token)
        delta = datetime.now() - password_request.createdAt
        one_day = 60 * 60 * 24
        if delta.seconds > one_day:
            password_request.delete()
            return render_template('auth/password_reset_request_expired.html')
    except Exception, e:
        print str(e)
        return render_template('auth/password_reset_request_expired.html')
    return render_template('auth/reset_password_form.html', token=token)


@flaskapp.route('/email_verification')
def email_verification():
    return render_template('account/email_verification.html')


@flaskapp.route('/password_updated')
def password_updated():
    return render_template('account/password_updated.html')


@flaskapp.route('/invalid_link')
def invalid_link():
    return render_template('account/invalid_link.html')


@flaskapp.route("/window")
def parse_iframe():
    return render_template('user_management.html')



@flaskapp.route('/_upload_scrapelisting', methods=['POST'])
def _upload_scrapelisting(request_json=None):
    print 'starting uploading listing'
    try:
        args = dict()
        j = request.json if not request_json else request_json
        #print 'received json', j
        
        coord = GeoPoint(latitude=float(j["location"]["lat"]), longitude=float(j["location"]["lng"]))
        place = Place(
            latLng=coord,
            country=j["country"],
            zipcode=str(j["zipcode"]),
            state=str(j["state"]),
            street=str(j["street"]),
            city=str(j["city"])
        )

        place.save()
        
        user = User.signup(j["email"], 'pleasechangeme')
        user.email = j['email']
        user.firstName = j["firstname"]
        user.lastName = j["lastname"]
        if user.lastName:
            user.fullName = "%s %s" % (j['firstname'], j['lastname'])
        else:
            user.fullName = j["firstname"]
        if j['phone']:
            user.phone = j['phone']
        print user    
        user.save()
        
        reviews = list()
        if j["reviews"]:
            for r in j["reviews"]:
                review = Review(
                    title=r["title"],
                    body=r["text"],
                    rating=str(r["rating"]),
                    location=r["location"],
                    date_stayed=r["date_stayed"],
                    datetime_submitted=Date(datetime.strptime(r["datetime_submitted"], '%Y-%m-%d')),
                    source=j["src"],
                    reviewer_name=r["reviewer"]["nickname"],
                    reviewer_avatar="http://res.cloudinary.com/djrymcpim/image/upload/v1456435570/adwetdm5q4dibhylgnzv.jpg",
                    reviewer_location=r["reviewer_location"]
                )
                reviews.append(review)
                review.save()
            
            print 'saved reviews'

        
        s_photos = j["photos"]
        print s_photos
        photos = list()
        for ph in s_photos:
            #large_url = imageuploader.upload_image(ph["uri"])
            #thumb_url = imageuploader.upload_image(ph["uri"])
            print ph["uri"]
            photo = Photo(
                caption=ph["caption"],
                large=ph["uri"],
                thumb=ph["uri"]
            )
            photo.save()
            photos.append(photo)

        print photos
        print 'saved photos'
        
        
        aa = j["amenities"]
        amens = list()
        for a in aa:
            if a["title"] == "Entertainment":
                for each in a["attributes"]:
                    amens.append(each)
            if  a["title"] == "General":
                for each in a['attributes']:
                    amens.append(each)
            if  a["title"] == "Kitchen":
                for each in a['attributes']:
                    amens.append(each)
            print amens
            print 'got amenities', amens
            house_rules = ''
            if a["title"] == "Suitability":
                for each in a['attributes']:
                    house_rules += each + '\n'     
        print amens            
        
               
        listing = Listing(
            bedrooms=j["bedrooms"],
            bathrooms=j["bathrooms"],
            reviewRating=j["avg_reviews"],
            reviewCount=j["num_reviews"],
            housingType=j["property_type"],
            accomodationFee=int(j["price"]),
            headline=j["headline"],
            placeDetails=place,
            cleaningFee=0, # look at this
            discountedRate=0,
            maxGuests=j["sleeps"],
            securityDeposit=0,
            taxRatePercentage=0,
            overviewText=j["description"],
            creator=user,
            photos=photos,
            reviews=reviews,
            houseRulesText=house_rules,
            amenities=amens,
            minNights=j["min_nights"],
            src=j["src"]
        )

        
        ids = listing.save()
        print ids
        mapping = ListingUrlMapping(
            listing=listing,
            id_vrbo=j["vrbo_url"],
            id_airbnb=""
        )

        mapping.save()
        
        user = User.Query.get(email=j["email"])
        print user
        listing_query = Listing.Query.get(creator=user)
        print listing_query.headline
        ob ={
            "_id": listing_query.objectId,
            "success":True
        }
        return json.dumps(ob)
    except Exception, e:
        print 'error', str(e)
        os.system('say "upload finished with error"')
        return str(e), 500

# @flaskapp.route("/reset_password")
# def reset_password():
#     return render_template('account/reset_password.html')


@flaskapp.route('/_upload_listing', methods=['POST'])
def upload_listing(request_json=None):
    print 'starting uploading listing'
    os.system('say "upload start"')
    try:
        j = request.json if not request_json else request_json
        print 'received json', j
        vrbo_url = j['id_vrbo'] if 'id_vrbo' in j else None
        airbnb_id = j['id_airbnb'] if 'id_airbnb' in j else None

        reqd_fields = ['email', 'firstname', 'lastname', 'city', 'state', 'street', 'zipcode', 'phone']
        for each in reqd_fields:
            if each not in j:
                print 'not in'
                return 'missing user info', 400

        pl = TuplePlace(
            city=j['city'],
            state=j['state'],
            zipcode=j['zipcode'],
            street=j['street'],
            country='United States'
        )

        if not vrbo_url and not airbnb_id:
            print 'not in'
            return 'no urls specified', 400
        print 'getting user'
        user = None
        try:
            user = User.Query.get(email=j['email'])
        except Exception, e:
            print 'error', str(e)
        if not user:
            user = User.signup(j['email'], 'pleasechangeme')
            user.email = j['email']
            user.firstName = j['firstname']
            user.lastName = j['lastname']
            if user.lastName:
                user.fullName = "%s %s" % (j['firstname'], j['lastname'])
            else:
                user.fullName = j['firstname']
            if j['phone']:
                user.phone = j['phone']
            user.save()

        print 'got user', user

        if airbnb_id:
            print 'scraping airbnb'
            s = airbnb_scraper.get_listing(airbnb_id)
            print '----------', s, vrbo_url
            if not s and vrbo_url:
                s = vrbo_scraper.get_listing(vrbo_url)
                listing = save_vrbo_listing(s, user, pl)
            else:
                print 'got site'
                listing = save_airbnb_listing(s, user)
        else:
            print 'scraping vrbo'
            s = vrbo_scraper.get_listing(vrbo_url)
            print 'got site'
            listing = save_vrbo_listing(s, user, pl)

        mapping = ListingUrlMapping(
            listing=listing,
            id_vrbo=vrbo_url,
            id_airbnb=airbnb_id
        )

        mapping.save()

        print 'done'
        os.system('say "upload finished"')
        return 'done'
    except Exception, e:
        print 'error', str(e)
        os.system('say "upload finished with error"')
        return str(e), 500


def save_vrbo_listing(s, user, pl=None):
    print s.location
    coord = GeoPoint(latitude=float(s.location.lat), longitude=float(s.location.lng))
    place = Place(
        latLng=coord,
        country=pl.country,
        zipcode=str(pl.zipcode),
        state=pl.state,
        street=pl.street,
        city=pl.city
    )

    place.save()
    print 'saved place', place
    # print 'looking at reviews', s
    reviews = list()

    if s.reviews:
        for r in s.reviews:
            avatar = imageuploader.upload_image(r.reviewer_avatar)
            review = Review(
                title=r.title,
                body=r.body,
                rating=r.rating,
                location=r.location,
                date_stayed=r.date_stayed,
                datetime_submitted=Date(datetime.strptime(r.datetime_submitted, '%Y-%m-%d')),
                source=r.source,
                reviewer_name=r.reviewer_name,
                reviewer_avatar=avatar,
                reviewer_location=r.reviewer_location
            )
            reviews.append(review)
            review.save()

    print reviews
    print 'saved reviews'

    s_photos = s.photos
    photos = list()
    for ph in s_photos:
        large_url = imageuploader.upload_image('http:' + ph.src)
        thumb_url = imageuploader.upload_image('http:' + ph.thumb)
        print large_url
        print thumb_url
        photo = Photo(
            caption=ph.caption,
            large=large_url,
            thumb=thumb_url
        )
        photo.save()
        photos.append(photo)

    print photos
    print 'saved photos'

    a = s.amenities
    amens = list()
    if 'Entertainment' in a:
        for each in a['Entertainment']:
            amens.append(each)
    if 'General' in a:
        for each in a['General']:
            amens.append(each)
    if 'Kitchen' in a:
        for each in a['Kitchen']:
            amens.append(each)

    print amens
    print 'got amenities', amens

    house_rules = ''

    if "Suitability" in a:
        for each in a['Suitability']:
            house_rules += each + '\n'

    listing = Listing(
        bedrooms=s.bedrooms,
        bathrooms=s.bathrooms,
        reviewRating=s.avg_reviews,
        reviewCount=s.num_reviews,
        housingType=s.property_type,
        accomodationFee=s.price,
        headline=s.headline,
        placeDetails=place,
        cleaningFee=0, # look at this
        discountedRate=0,
        maxGuests=s.sleeps,
        securityDeposit=s.security_deposit if hasattr(s, 'security_deposit') and s.security_deposit else 0,
        taxRatePercentage=s.tax_rate if hasattr(s, 'tax_rate') and s.tax_rate else 0,
        overviewText=s.description,
        creator=user,
        photos=photos,
        reviews=reviews,
        houseRulesText=house_rules,
        amenities=amens,
        petsAllowed=s.pets_allowed,
        src='Vrbo'
    )

    print listing
    listing.save()
    return listing


def save_airbnb_listing(s, user, pl=None):
    print s.location
    coord = GeoPoint(latitude=float(s.location.lat), longitude=float(s.location.lng))
    place = Place(
        latLng=coord,
        city=s.city,
        country=s.country,
        zipcode=str(s.zipcode),
        state=s.state,
        street=s.address.split(',')[0] if s.address else None
    )
    place.save()
    print 'saved place', place.__dict__
    # print 'looking at reviews', s
    reviews = list()

    if s.reviews:
        for r in s.reviews:
            m = re.search('([0-9]+-[0-9]+-[0-9]+)T', r.datetime_submitted)
            if m:
                date_string = m.group(1)
                d = Date(datetime.strptime(date_string, '%Y-%m-%d'))
            else:
                d = None

            avatar = imageuploader.upload_image(r.reviewer_avatar)
            review = Review(
                title=r.title,
                body=r.body,
                rating=r.rating,
                location=r.location,
                date_stayed=r.date_stayed,
                datetime_submitted=d,
                source=r.source,
                reviewer_name=r.reviewer_name,
                reviewer_avatar=avatar,
                reviewer_location=r.reviewer_location
            )
            reviews.append(review)
            review.save()

    print reviews
    print 'saved reviews'

    s_photos = s.photos
    photos = list()
    for ph in s_photos:
        large_url = imageuploader.upload_image(ph.src)
        thumb_url = imageuploader.upload_image(ph.thumb)
        print large_url
        print thumb_url
        photo = Photo(
            caption=ph.caption,
            large=large_url,
            thumb=thumb_url
        )
        photo.save()
        photos.append(photo)

    print photos
    print 'saved photos'

    amens = s.amenities

    print amens
    print 'got amenities', amens

    print s.bedrooms, s.bathrooms, s.avg_reviews, s.price, s.cleaning_fee, s.security_deposit, s.price_extra_person, s.price_monthly
    listing = Listing(
        bedrooms=s.bedrooms,
        bathrooms=s.bathrooms,
        reviewRating=s.avg_reviews,
        reviewCount=s.num_reviews,
        housingType=s.property_type,
        accomodationFee=s.price,
        headline=s.headline,
        placeDetails=place,
        cleaningFee=s.cleaning_fee, # look at this
        discountedRate=0,
        maxGuests=s.sleeps,
        securityDeposit=s.security_deposit if hasattr(s, 'security_deposit') and s.security_deposit else 0,
        taxRatePercentage=s.tax_rate if hasattr(s, 'tax_rate') and s.tax_rate else 0,
        overviewText=s.summary,
        creator=user,
        photos=photos,
        reviews=reviews,
        houseRulesText=s.house_rules,
        amenities=amens,
        neighborhoodText=s.neighborhood,
        placeText=s.space,
        moreDetailsText=s.description,
        gettingAroundText=s.transit_info,
        priceExtraPesons=s.price_extra_person,
        priceMonthly=s.price_monthly,
        minNights=s.min_nights,
        src='Airbnb'
    )

    listing.save()
    return listing


@flaskapp.route('/_upload_listings', methods=['POST'])
def upload_listings():
    pass


@flaskapp.route('/search', methods=['GET'])
def get_listings_by_locality():
    city = request.args.get('city', '')
    state = request.args.get('state', '')
    print 'got', city, state
    listings = Listing.Query.all().select_related("placeDetails", "photos")
    ret = list()
    for each in listings:
        if each.placeDetails.city == city and each.placeDetails.state == state:
            ret.append(each)
    print ret
    return render_template('search.html', listings=ret, city=city, state=state)



@flaskapp.route("/_submit_for_settlement", methods=['POST'])
def charge_customer():
    try:
        reservation_id = request.form.get('reservation_id')
        reservation = Reservation.Query.filter(objectId=reservation_id).select_related("renter")[0]
        user = reservation.renter
        b = Billing.Query.get(user=user)
        customer_id = b.customerId
        success = payment.create_transaction(customer_id, reservation)
        success = True
        if success:
            reservation.approved = True
            reservation.save()
            mailer.send_reservation_approved_confirmation(reservation)
        else:
            reservation.approved = False
            reservation.error = True
            reservation.save()
        return jsonify(dict(success=success))
    except Exception, e:
        return jsonify(dict(success=False, message=e.message))


@flaskapp.route("/_deny_reservation", methods=['POST'])
def deny_reservation():
    try:
        reservation_id = request.form.get('reservation_id')
        reservation = Reservation.Query.filter(objectId=reservation_id).select_related("renter")[0]
        user = reservation.renter
        # b = Billing.Query.get(user=user)
        # customer_id = b.customerId
        # # success = payment.create_transaction(customer_id, reservation)
        # success = True
        reservation.approved = False
        reservation.save()
        mailer.send_reservation_denied_confirmation(reservation)
        return jsonify(dict(success=True))
    except Exception, e:
        return jsonify(dict(success=False, message=e.message))


def charge_customer_with_reservation(reservation):
    print 'charge_customer', reservation
    success = payment.create_and_submit_transaction(reservation)
    print success
    return success


def get_billing(user_id):
    b = None
    try:
        b = Billing.Query.get(User(objectId=user_id))
    except Exception, e:
        print str(e)
        raise Exception("Could not find billing object: %s" % e)
    return b


@flaskapp.route('/sms/reply', methods=['POST'])
def twilio_callback():
    print request.values
    phone = request.values.get('From')
    body = request.values.get('Body')
    # TODO validate phone and body
    reply_id = body
    print phone, body
    try:
        user = User.Query.get(phone=phone)
        print 'got user', user
        reservations = Reservation.Query.all().filter(reservation_reply_id=int(reply_id)).select_related('listing')
        print reservations
        reservation = None
        for r in reservations:
            if r.listing.creator.objectId == user.objectId:
                reservation = r
                break
        print 'got reservation', reservation
        reservation.approved = True
        reservation.save()
        success = charge_customer_with_reservation(reservation)
        print 'success', success
        if success:
            reservation.approved = True
            reservation.save()
            mailer.send_reservation_approved_confirmation(reservation)
        else:
            reservation.approved = False
            reservation.error = True
            reservation.save()
    except Exception, e:
        print 'error:', str(e)
    return 'yuay' #todo


@flaskapp.route('/sms/status', methods=['POST'])
def twilio_status():
    from pprint import pprint
    pprint(request.__dict__)

    return 'yay'


@flaskapp.route('/test_conf', methods=['GET'])
def test_confirmation():
    reservation = Reservation.Query.all().select_related("listing.photos")[-1]
    print reservation
    return transform(render_template("mailer/reservation_request_confirmation.html", reservation=reservation))


@flaskapp.route("/api/census/RecordHit", methods=['POST'])
def record_hit():
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@flaskapp.route('/test_500', methods=['GET'])
def test():
    raise Exception('test')


@flaskapp.route('/test_404', methods=['GET'])
def test_404():
    return '', 404


@flaskapp.errorhandler(404)
def handle_four(e):
    return render_template('error/404.html'), 404


@flaskapp.errorhandler(500)
def handle_five(e):
    return render_template('error/500.html'), 500


@flaskapp.route('/taro')
def taro():
    return render_template('error/500.html')


@flaskapp.route('/resend_email')
def resend_email():
    try:
        user = g.user
        v = Verification.Query.get(user=user)
    except:
        v = Verification(user=user)
        v.save()
    mailer.send_user_verification_mail(user.email, user.firstName, v.objectId)
    return render_template('account/please_verify_account.html')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        if not hasattr(g.user, 'accountVerified') or not g.user.accountVerified:
            try:
                v = Verification.Query.get(user=g.user)
                if v.verified:
                    g.user.accountVerified = True
                    g.user.save()
                v.delete()
                return f(*args, **kwargs)
            except:
                pass
            return render_template('account/please_verify_account.html')
        return f(*args, **kwargs)
    return decorated_function


@flaskapp.before_request
def before_request():
    try:
        with SessionToken(session['session_id']):
            user = User.current_user()
            g.user = user
            return
    except:
        pass
    g.user = None


@flaskapp.route('/privacypolicy')
def privacy_policy():
    return render_template('privacy_policy.html')


@flaskapp.route('/tos')
def terms_of_service():
    return render_template('tos.html')


@flaskapp.route('/careers')
def careers():
    return render_template('careers.html')

@flaskapp.route('/playground')
def playground():
    return render_template('playground.html')


@flaskapp.route('/twilio/verify', methods=['POST'])
def twilio_verify():
    from twilio import twiml
    resp = twiml.Response()
    print 'got resp: ', resp
    number = os.environ.get('TWILIO_VERIFY_NUMBER')
    print 'GOT NUMBER', number
    resp.addPause(length=2)
    resp.play('', ''.join(['ww'+x for x in number]))
    resp.addPause(length=10)
    # resp.addDial(number if number else '45').number('6266674386', sendDigits=number)
    print resp
    return str(resp)