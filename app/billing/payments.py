import braintree
from parse_rest.user import User

from app.billing.braintree_payments import BraintreePayments
from app.billing.exceptions import PaymentsException
from app.models.parse import Billing

SANDBOX = dict(
    environment=braintree.Environment.Sandbox,
    merchant_id='p5cvbnzmfrdxh2ys',
    public_key='5q94bc8dspdsc2j7',
    private_key='c4854f6f29f45ef3147a57aac501c181'
)

PRODUCTION = dict(
    environment=braintree.Environment.Production,
    merchant_id='yqhsqsm8h9qjrq23',
    public_key='yjjvyx5tt29g8kvn',
    private_key='a433a041e2de0f2ade55f1a0a91d2d78'
)

"""

Manager that handles calls to the payment module and transforms the data if necessary
"""


class PaymentsManager:
    def __init__(self, keys):
        self.keys = keys
        self.payments_method = BraintreePayments(**keys)

    def get_client_token(self, user_id=None):
        if user_id:
            try:
                user = User(objectId=user_id)
                b = Billing.Query.get(user=user)
                customer_id = b.customerId
                return self.payments_method.generate_client_token(customer_id=customer_id)
            except Exception, e:
                print str(e), 'cannot find customer Id'
        return self.payments_method.generate_client_token()

    def create_customer_profile(self, user, payment_nonce):
        try:
            result = self.payments_method.create_customer_and_authorize(
                user.email,
                payment_nonce,
                user.firstName,
                user.lastName,
                user.phone if hasattr(user, 'phone') else ''
            )
            return result
        except Exception, e:
            raise PaymentsException(e.message)

    def create_transaction(self, customer_id, reservation):
        payment_amt = reservation.total
        try:
            self.payments_method.create_and_submit_transaction(customer_id, payment_amt)
            return True
        except Exception, e:
            raise PaymentsException(e.message)

    def charge_customer_pending_transaction(self, reservation):
        result = self.payments_method.collect(reservation.transactionId)
        return result
