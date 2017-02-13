"""

Thrown exception for uncaught exceptions
"""


class UncaughtException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


"""

Thrown exception for card declined error sent by the payment module
"""


class CardDeclined(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


"""

Thrown exception for misc errors regarding payments
"""


class PaymentsException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
