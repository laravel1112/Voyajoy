from functools import wraps
from flask import g, request, redirect, url_for

"""

Checks a flask request to see if the user is logged in
If not, redirect to login
"""


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function
