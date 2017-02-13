from flask import render_template

from app import flaskapp


@flaskapp.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", 404)


@flaskapp.errorhandler(401)
def unauthorized(error):
    return render_template("401.html", 401)

