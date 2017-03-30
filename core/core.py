#!/usr/bin/env python
from flask import Flask
import os
import sys
import datetime
import multiprocessing

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
import web
import views
import models, database, settings, utils

app = web.app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6002, debug=True)
