import os

import sendgrid
from flask import render_template
from premailer import transform

from app.util.dateutil import get_friendly_from_parse_date

"""
This file communicates with sendgrid to send email notifications.

"""
sg = sendgrid.SendGridClient(os.environ.get("SENDGRID_USERNAME", ""), os.environ.get('SENDGRID_PASSWORD', ""))
SENDER = 'Voyajoy Support <support@voyajoy.com>'


def send_booking_confirmation(reservation, args):
    subject = 'Your Voyajoy Booking Confirmation %s %s' % (reservation.arrivalDate, reservation.departureDate)
    _send_message(
        reservation.renter.email,
        subject,
        html=render_template('mailer/reservation_confirmation.html', reservation=reservation, **args))


def send_user_verification_mail(email, first_name, token, next=None):
    subject = "Please verify your email address"
    _send_message(
        email,
        subject,
        html=render_template(
            'mailer/email_verification.html',
            first_name=first_name,
            token=token,
            next=next
        )
    )


def send_user_welcome_mail(user):
    subject = 'Welcome to Voyajoy'
    url = 'http://www.voyajoy.com/login'
    args = dict(
        url=url,
        user=user
    )
    _send_message(user.email, subject, html=render_template('mailer/user_welcome.html', **args))


def _send_message(recipient, subject, text='', html=''):
    message = sendgrid.Mail(to=recipient,
                            subject=subject,
                            html=transform(html),
                            text=text,
                            from_email=SENDER
                            )
    status, msg = sg.send(message)
    print status, msg


def send_request_reservation_confirmation(reservation):
    subject = 'Your Voyajoy Booking Request for %s through %s' % (
        get_friendly_from_parse_date(reservation.arrivalDate, True),
        get_friendly_from_parse_date(reservation.departureDate, True)
    )
    _send_message(
        reservation.renter.email,
        subject,
        html=render_template('mailer/reservation_request_confirmation.html', reservation=reservation))


def send_password_reset_request(email, first_name, token):
    subject = 'Reset your password'
    _send_message(
        email,
        subject,
        html=render_template('mailer/reset_password.html', first_name=first_name, token=token)
    )


def send_request_reservation_notification(reservation):
    subject = '%s wants to rent from %s through %s' % (
        reservation.renter.email,
        get_friendly_from_parse_date(reservation.arrivalDate, True),
        get_friendly_from_parse_date(reservation.departureDate, True)
    )
    _send_message(
        'inquiries@voyajoy.com',
        subject,
        html=render_template('mailer/reservation_request_confirmation.html', reservation=reservation))


def send_reservation_approved_confirmation(reservation):
    subject = 'Your Voyajoy Booking Request was approved for %s through %s' % (
        get_friendly_from_parse_date(reservation.arrivalDate, True),
        get_friendly_from_parse_date(reservation.departureDate, True)
    )
    _send_message(
        reservation.renter.email,
        subject,
        html=render_template('mailer/reservation_approved_confirmation.html', reservation=reservation))


def send_reservation_denied_confirmation(reservation):
    subject = 'Your Voyajoy Booking Request for %s through %s' % (
        get_friendly_from_parse_date(reservation.arrivalDate, True),
        get_friendly_from_parse_date(reservation.departureDate, True)
    )
    _send_message(
        reservation.renter.email,
        subject,
        html=render_template('mailer/reservation_denied_confirmation.html', reservation=reservation))
    return None
