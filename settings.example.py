# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytz
import datetime

DB_URL = 'sqlite:///data/compiler.db'
FLASK_SECRET_KEY = 'you can copy from: python -c "print(repr(__import__(\"os\").urandom(30)))"'
TIMEZONE = pytz.timezone('Asia/Shanghai')
WEBROOT = '/compiler2017'
TEST_PHASES = [
    'syntax pretest', 'syntax extended',
    'semantic pretest', 'semantic extended',
    'codegen pretest', 'codegen extended',
    'optimization pretest', 'optimization extended'
]
ARCHIVED = False
CORE_URL = ''
CORE_BUILD_LOG_PATH = ''
CORE_TESTRUN_STDERR_PATH = ''
LOG_LENGTH_LIMIT = 10240
JUDGE_TOKEN = 'you can copy from: python -c "print(repr(__import__(\"os\").urandom(30)))"'
JUDGE_BUILD_TIMEOUT = 60
JUDGE_GIT_REPO_PATH = ''
JUDGE_REQUEST_TIMEOUT = 5
