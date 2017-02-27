from flask import Flask
import os
import sys
import datetime

import models, database, settings, utils

app = Flask(__name__, static_url_path=settings.WEBROOT + '/static')
app.secret_key = settings.FLASK_SECRET_KEY
app.jinja_env.filters['format_from_utc'] = utils.format_from_utc
app.jinja_env.filters['nl2p'] = utils.nl2p
app.jinja_env.globals.update(datetime=datetime.datetime)
app.jinja_env.globals.update(len=len)
app.jinja_env.globals.update(max=max)
app.jinja_env.globals.update(zip=zip)

@app.teardown_appcontext
def shutdown_session(exception=None):
    database.db_session.remove()
