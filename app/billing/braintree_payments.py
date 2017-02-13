import braintree

# https://developers.braintreepayments.com/guides/customers/python

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

Braintree module
Handles api calls to braintree to create customers and make payments
"""
class BraintreePayments:
    def __init__(self, environment, merchant_id, public_key, private_key):
        braintree.Configuration.configure(
            environment,
            merchant_id=merchant_id,
            public_key=public_key,
            private_key=private_key
        )

    @staticmethod
    def generate_client_token(*args, **kwargs):
        return braintree.ClientToken.generate(params=kwargs)

    @staticmethod
    def create_customer_and_authorize(email, payment_nonce, first_name, last_name, phone):
        result = braintree.Customer.create({
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            "credit_card": {
                "payment_method_nonce": payment_nonce,
                "options": {
                    "verify_card": True,
                }
            }
        })
        print result

        if not result.is_success:
            raise Exception(result.message)
        return result.customer.id


    @staticmethod
    def create_customer(email, first_name, last_name, phone):
        result = braintree.Customer.create({
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
        })

        success = result.is_success
        customer_id = result.customer.id

        print success, customer_id
        print result
        return result

    @staticmethod
    def delete_customer(customer_id):
        result = braintree.Customer.delete(customer_id)
        print result.is_success
        return result.is_success

    @staticmethod
    def create_and_submit_transaction(customer_id, amount):
        result = braintree.Transaction.sale({
            'customer_id': customer_id,
            'amount': int(amount),
            'options': {
                "submit_for_settlement": True
            },
        })
        if not result.is_success:
            raise Exception(result.message)
        return True

    @staticmethod
    def _is_result_successful(result):
        return result.is_success

    @staticmethod
    def collect(transaction_id):
        result = braintree.Transaction.submit_for_settlement(transaction_id)
        return result

    @staticmethod
    def void_transaction(transaction_id):
        result = braintree.Transaction.void(transaction_id)
        if result.is_success:
            print result.is_success

    @staticmethod
    def refund_transaction(transaction_id):
        result = braintree.Transaction.refund(transaction_id)
        print result.is_sucess

    @staticmethod
    def get_transaction(transaction_id):
        result = braintree.Transaction.find(transaction_id)
        return result

    @staticmethod
    def get_customer(customer_id):
        result = braintree.Customer.find(customer_id)
        return result