from app import flaskapp
from twilio.rest import TwilioRestClient

"""

This file communicates with twilio API's to send sms notifications
"""

ACCOUNT_SID = 'AC64fe41259eca5f10675a01174e5a1147'
AUTH_TOKEN = '9e3a8de6cc68686bb8282e188c053c59'
FROM = '+16502854948'

client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)


def create_message(phone, body):
    return client.messages.create(
        to='+16268645237',
        from_=FROM,
        body=body
    )


@flaskapp.route('/test_twilio')
def test_twilio():
    message = create_message('6268645237',
                             'Martha Stewart wants to destroy your house, please respond with \'yes\' to accept')
    print message
    print vars(message)
    return str(message)
