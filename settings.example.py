# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytz
import datetime
BASEDIR = os.path.realpath(os.path.dirname(__file__))

### Core Settings
DB_URL = 'postgresql+psycopg2://compiler2017:mypassword@localhost/compiler2017'
# DB_URL = 'sqlite:///data/compiler.db'
TIMEZONE = pytz.timezone('Asia/Shanghai')
TEST_PHASES = [
    'semantic pretest', 'semantic extended',
    'codegen pretest', 'codegen extended',
    'optim pretest', 'optim extended'
]
JUDGE_TOKEN = 'you can copy from: python -c "print(repr(__import__(\"os\").urandom(30)))"'
CORE_BUILD_LOG_PATH = os.path.join(BASEDIR, 'data', 'build')
CORE_TESTRUN_STDERR_PATH = os.path.join(BASEDIR, 'data', 'testrun')

### Website Settings
WEBSITE_NAME = 'Compiler 2017'
WEBROOT = '/compiler2017'
# FINAL_ROOT = WEBROOT + '/static/final'  # if the final result has been generated
FINAL_ROOT = None                         # if not final yet
BUILDS_PER_PAGE = 20
RUNS_PER_PAGE = 30
CORE_PORT = 6002
HOMEPAGE_TITLE = "Hello, Compiler 2017"
HOMEPAGE_DESCRIPTION = '''
<p>
  Enjoy writing compilers.
</p>
Please do
  <ul>
    <li>Make use of the online judge. Commit frequently!</li>
    <li>Report bugs if you find them</li>
  </ul>
Please do not
  <ul>
    <li>Exploit bugs of the online judge.</li>
    <li>Steal non-public testcases in any form (for example, print them to stderr)</li>
  </ul>
Information:
  <ul>
    <li>Source code build time (i.e. the time taken to build your compiler): at most 30 seconds</li>
    <li>Compile time (i.e. the time your compiler runs): at most 5 seconds</li>
    <li>Memory usage: at most 256MB</li>
    <li>Java version: Oracle JDK 1.8.0 Update 121</li>
    <li>g++ version: 5.4.0</li>
  </ul>
<hr>
Some Links:
<ul>
  <li><a href="https://acm.sjtu.edu.cn/wiki/Compiler_2017">Compiler 2017 Course Wiki</a></li>
  <li><a href="https://bitbucket.org/acmcompiler/compiler2017-demo/src">How to make my compiler run on the Online Judge</a></li>
  <li><a href="https://github.com/abcdabcd987/acm-compiler-judge/blob/master/docs/use_guide.md">How to Use the Online Judge</a></li>
  <li><a href="https://github.com/abcdabcd987/acm-compiler-judge/blob/master/docs/testcase_guide.md">How to Contribute a Testcase</a></li>
  <li><a href="https://bitbucket.org/acmcompiler/compiler2017-testcases">Git repository of testcases (may not be up-to-date as the Online Judge)</a></li>
</ul>
'''

### Judge Settings
JUDGE_NAME = 'Judge 1'
JUDGE_BUILD_TIMEOUT = 60
JUDGE_REQUEST_TIMEOUT = 5
JUDGE_COMPILE_TIMEOUT = 15
JUDGE_RUN_TIMES_PER_TEST = 3
JUDGE_RUN_MEMORY_LIMIT = '512m'
LOG_LENGTH_LIMIT = 4096
CORE_URL = 'http://localhost:{}{}'.format(CORE_PORT, WEBROOT)
JUDGE_GIT_REPO_PATH = os.path.join(BASEDIR, 'data', 'repo')
JUDGE_TESTCASE_PATH = os.path.join(BASEDIR, 'data', 'testcase')

