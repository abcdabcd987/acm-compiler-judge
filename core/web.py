from flask import Flask
import os
import sys
import datetime

import models, database, settings, utils

app = Flask(__name__, static_url_path=settings.WEBROOT + '/static')
app.jinja_env.filters['format_from_utc'] = utils.format_from_utc
app.jinja_env.filters['nl2p'] = utils.nl2p
app.jinja_env.filters['nl2monobr'] = utils.nl2monobr
app.jinja_env.filters['multiline_indent'] = utils.multiline_indent
app.jinja_env.filters['testcase_tooltip'] = utils.testcase_tooltip
app.jinja_env.filters['label_class'] = utils.label_class
app.jinja_env.filters['phase_to_index'] = utils.phase_to_index
app.jinja_env.filters['version_count_tooltip'] = utils.version_count_tooltip
app.jinja_env.filters['time_from_now'] = utils.time_from_now
app.jinja_env.globals.update(datetime=datetime.datetime)
app.jinja_env.globals.update(len=len)
app.jinja_env.globals.update(map=map)
app.jinja_env.globals.update(str=str)
app.jinja_env.globals.update(max=max)
app.jinja_env.globals.update(zip=zip)
app.jinja_env.globals.update(reversed=reversed)
app.jinja_env.globals.update(website_name=settings.WEBSITE_NAME)
app.jinja_env.globals.update(test_phases=settings.TEST_PHASES)
app.jinja_env.globals.update(homepage_title=settings.HOMEPAGE_TITLE)
app.jinja_env.globals.update(homepage_description=settings.HOMEPAGE_DESCRIPTION)
app.jinja_env.globals.update(FINAL_ROOT=settings.FINAL_ROOT)

@app.teardown_appcontext
def shutdown_session(exception=None):
    database.db_session.remove()
