import logging
import sys

from flask import Flask
from flask.ext.sslify import SSLify
from parse_rest.connection import register

flaskapp = Flask(__name__)
sslify = SSLify(flaskapp)
flaskapp.config.from_pyfile('default.cfg')
flaskapp.logger.addHandler(logging.StreamHandler(sys.stdout))
flaskapp.logger.setLevel(logging.ERROR)
flaskapp.secret_key = flaskapp.config['APP_SECRET_KEY']
from app.billing import payments

payment = payments.PaymentsManager(payments.PRODUCTION)
from app import views
register(flaskapp.config['PARSE_API_KEY'], flaskapp.config['PARSE_SECRET_KEY'])

from app import pidgeon
from app.views import reservations, views
from app.scripts import ratings_uploader
