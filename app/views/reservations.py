from datetime import datetime
from functools import wraps

from flask import request, render_template, jsonify, url_for, g, session
from parse_rest.datatypes import Date
from werkzeug.utils import redirect

from app import flaskapp, payment
from app import fuzion
from app import mailer, pidgeon
from app.calendar import airbnb_calendar
from app.models.parse import Reservation, ListingUrlMapping, ReservationSmsCounter, Billing
from app.calendar import vrbo_calendar
from app.util.dateutil import get_date_delta_days, get_datetime, get_friendly_from_parse_date
from app.views.views import Listing, login_required


def verify_availability(start, end, listing_id, num_guests):
    response = fuzion.get_availability(start, end, listing_id, num_guests)
    return response['available']


def get_book_request_proxy():
    try:
        return get_book_request()
    except Exception, e:
        print str(e)
        return '', 401


def record_url_to_redirect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user:
            session['redirect_booking_target'] = request.url
        return f(*args, **kwargs)

    return decorated_function


@flaskapp.route('/reservation/<reservation_id>')
@login_required
def reservation(reservation_id):
    try:
        r = Reservation.Query.get(objectId=reservation_id)
        if r.renter.objectId != g.user.objectId:
            return '', 404
    except Exception, e:
        print str(e)
        return '', 404
    return render_template("reservation_receipt.html", reservation=r)


@flaskapp.route('/request/<reservation_id>/confirmation')
@login_required
def request_confirmation(reservation_id):
    try:
        r = Reservation.Query.get(objectId=reservation_id)
        if r.renter.objectId != g.user.objectId:
            return '', 404
    except Exception, e:
        print str(e)
        return '', 404
    return render_template("reservation.html", reservation=r)


@flaskapp.route('/request')
@login_required
def get_book_request():
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    num_guests = request.args.get('num_guests', '1')
    print num_guests
    listing_id = request.args.get('id')
    start = get_datetime(start_date)
    end = get_datetime(end_date)
    num_nights = get_date_delta_days(start, end)

    if not listing_id:
        return redirect(url_for('index'))

    if not verify_availability(start_date, end_date, listing_id, num_guests):
        return '', 204

    listing = Listing.Query.filter(objectId=listing_id).select_related("photos")[0]
    mapping = ListingUrlMapping.Query.get(listing=listing)

    discount_per_night = float(listing.discountedRate) / 100 * listing.accomodationFee
    total_discount = discount_per_night * num_nights
    rental_fee_total_without_discount = listing.accomodationFee * num_nights
    rental_fee_total_with_discount = rental_fee_total_without_discount - total_discount
    total = 0
    airbnb_pricing = None
    if flaskapp.config['USE_DYNAMIC_PRICING']:
        airbnb_pricing = airbnb_calendar.get_pricing(start_date, end_date, mapping.id_airbnb, num_guests)
        to_sum = [x['price']['local_price'] for x in airbnb_pricing]
        total = sum(to_sum)
        if total:
            rental_fee_total_without_discount = total
            rental_fee_total_with_discount = total - (float(listing.discountedRate) / 100 * total)

    if listing.discountedRate:
        total = rental_fee_total_with_discount
    else:
        total = rental_fee_total_without_discount
    total += listing.cleaningFee
    taxes = total * (listing.taxRatePercentage / 100)
    total *= (1 + (listing.taxRatePercentage / 100))

    total += listing.securityDeposit
    parse_start = Date(start)
    parse_end = Date(end)
    try:
        reservation_counter = ReservationSmsCounter.Query.get(user=listing.creator)
        counter = reservation_counter.counter
        counter += 1
        reservation_counter.counter = counter
        reservation_counter.save()
    except Exception, e:
        print 'error:', str(e), type(e)
        reservation_counter = ReservationSmsCounter(user=listing.creator, counter=1)
        reservation_counter.save()
        counter = 1

    r = Reservation(
        taxes=taxes,
        total=total,
        listing=listing,
        renter=g.user,
        rentalFee=listing.accomodationFee,
        pricingDaysJson=airbnb_pricing,
        numNights=num_nights,
        numGuests=num_guests,
        cleaningFee=listing.cleaningFee,
        taxRate=listing.taxRatePercentage,
        securityDeposit=listing.securityDeposit,
        arrivalDate=parse_start,
        departureDate=parse_end,
        discountedRate=listing.discountedRate,
        rentalFeeTotalWithoutDiscount=rental_fee_total_without_discount,
        rentalFeeTotalWithDiscount=rental_fee_total_with_discount,
        totalDiscount=total_discount,
        discountPerNight=discount_per_night,
        completed=False,
        reservation_reply_id=counter,
        approved=False,
    )
    r.save()

    return render_template(
        '/booking.html',
        reservation=r,
        arrival=get_friendly_from_parse_date(parse_start),
        departure=get_friendly_from_parse_date(parse_end),
        customer_token=payment.get_client_token(g.user.objectId)
    )


def send_inquiry_text(reservation):
    user = reservation.listing.creator
    renter = reservation.renter.firstName
    counter = reservation.reservation_reply_id
    reply_id = counter
    template = 'Hi {owner}, {renter} wants to stay at your home on {arrival} until {departure} ({days}) for ${price}. Reply with {reply_id} to accept {renter}\'s request'
    message = template.format(
        owner=user.firstName,
        renter=renter,
        days='%s night' % reservation.numNights if reservation.numNights == 1 else '%s nights' % reservation.numNights,
        arrival=get_friendly_from_parse_date(reservation.arrivalDate),
        departure=get_friendly_from_parse_date(reservation.departureDate),
        price=reservation.total,
        reply_id=reply_id
    )
    text = pidgeon.create_message(user.phone, message)
    print text


@flaskapp.route("/_is_reservation_completed/<reservation_id>", methods=['GET'])
def is_reservation_completed(reservation_id):
    try:
        r = Reservation.Query.get(objectId=reservation_id)
        print reservation_id, r.objectId, r.completed
        return jsonify(dict(success=True, completed=r.completed, target=url_for('dashboard')))
    except Exception, e:
        return jsonify(dict(success=False, message=str(e)))


@flaskapp.route("/checkout", methods=['POST'])
@login_required
def complete_reservation_request():
    try:
        reservation_id = request.form['reservation_id']
        nonce = request.form['payment_method_nonce']
        r = Reservation.Query.filter(objectId=reservation_id).select_related('listing', 'listing.photos')[0]
        if r.completed:
            return jsonify(dict(success=True, target=url_for('dashboard')))
        print 'completed?', r.completed
        try:
            b = Billing.Query.get(user=g.user)
        except Exception, e:
            customer_id = payment.create_customer_profile(r.renter, nonce)
            b = Billing(user=r.renter, customerId=customer_id)
            b.save()
        mailer.send_request_reservation_confirmation(r)
        mailer.send_request_reservation_notification(r)
        r.completed = True
        # r.cc_last_four = 'xxxx'
        r.save()
        if flaskapp.config.get('RESERVATION_INQUIRY_MANAGEMENT_VIA_SMS', False) and hasattr(r.listing.creator,
                                                                                            'phone') and r.listing.creator.phone:
            send_inquiry_text(r)
        return jsonify(dict(success=True, target=url_for('request_confirmation', reservation_id=reservation_id)))
    except Exception, e:
        return jsonify(dict(success=False, message=e.message))


@flaskapp.route('/_is_available')
def is_dates_available():
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    num_guests = request.args.get('num_guests', '1')
    listing_id = request.args.get('listing_id', '')
    response = fuzion.get_availability(start_date, end_date, listing_id, num_guests)
    print response
    return jsonify(response)


@flaskapp.route('/_get_pricing')
def get_pricing():
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    listing_id = request.args.get('listing_id', '')
    num_guests = request.args.get('num_guests', '')
    if listing_id:
        listing = Listing(objectId=listing_id)
        mapping = ListingUrlMapping.Query.get(listing=listing)
        results = airbnb_calendar.get_pricing(start_date, end_date, mapping.id_airbnb, num_guests)
        total = 0
        for each in results:
            total += each['price']['local_price']
        print total
        response = dict(success=True if results else False, totalPrice=total, results=results)
        return jsonify(response)
    return {}


@flaskapp.route('/_get_calendar')
def get_calendar():
    print 'starting isavailable'
    try:
        listing_id = request.args.get('listing_id', '')
        start_date = request.args.get('start_date', datetime.now())
        listing = Listing()
        listing.objectId = listing_id
        print listing
        mapping = ListingUrlMapping.Query.get(listing=listing)
        print mapping
        print listing_id
        if mapping.id_airbnb:
            response = airbnb_calendar.get_calendar(mapping.id_airbnb, start_date)
            print 'found airbnb calendar', response
        elif mapping.id_vrbo:
            response = vrbo_calendar.get_calendar(mapping.id_vrbo)
            print 'found vrbo calendar', response
        else:
            print 'could not find any url'
            response = list()
        print response
        return jsonify(dict(results=response if response else list()))
    except Exception, e:
        print 'error', str(e)
        return jsonify(dict(results=list()))


@flaskapp.route("/dashboard")
@login_required
def dashboard():
    reservations = Reservation.Query.all().filter(renter=g.user, completed=True).select_related("listing",
                                                                                                "listing.photos")
    if not reservations:
        return redirect(url_for('index'))

    return render_template('dashboard.html', reservations=reservations)


@flaskapp.route("/_get_reservation_dashboard")
@login_required
def reservation_dashboard():
    reservations = Reservation.Query.all().filter(renter=g.user, completed=True).select_related("listing",
                                                                                                "listing.photos")
    return render_template('dashboard_reservation_module.html', reservations=reservations)


@flaskapp.route("/_get_listings_dashboard")
@login_required
def listings_dashboard():
    listings = Listing.Query.all().filter(creator=g.user).select_related('photos', 'placeDetails')
    return render_template('dashboard_listings_module.html', listings=listings)


@flaskapp.route("/_get_account_dashboard")
@login_required
def account_dashboard():
    reservations = Reservation.Query.all().filter(renter=g.user, completed=True).select_related("listing",
                                                                                                "listing.photos")
    return render_template('dashboard_account_module.html', reservations=reservations)
