# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytz
import datetime

WEBSITE_NAME = 'Compiler 2017'
BUILDS_PER_PAGE = 20
RUNS_PER_PAGE = 50
DB_URL = 'sqlite:////tmp/compiler.db'
TIMEZONE = pytz.timezone('Asia/Shanghai')
WEBROOT = '/compiler2017'
HOMEPAGE_TITLE = "Hello, Compiler 2017"
HOMEPAGE_DESCRIPTION = '''
<p>Enjoy writing compilers.</p>
'''
TEST_PHASES = [
    'semantic pretest', 'semantic extended',
    'codegen pretest', 'codegen extended',
    'optim pretest', 'optim extended'
]
ARCHIVED = False
CORE_URL = 'http://localhost:6002' + WEBROOT
CORE_BUILD_LOG_PATH = '/tmp/core/build'
CORE_TESTRUN_STDERR_PATH = '/tmp/core/testrun'
LOG_LENGTH_LIMIT = 10240
JUDGE_NAME = 'Judge 1'
JUDGE_TOKEN = 'you can copy from: python -c "print(repr(__import__(\"os\").urandom(30)))"'
JUDGE_BUILD_TIMEOUT = 60
JUDGE_GIT_REPO_PATH = '/tmp/judge/git'
JUDGE_TESTCASE_PATH = '/tmp/judge/testcase'
JUDGE_REQUEST_TIMEOUT = 5
JUDGE_COMPILE_TIMEOUT = 15
JUDGE_RUN_TIMES_PER_TEST = 3
