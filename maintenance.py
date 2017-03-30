#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
import os
import sys
import time
import json
import codecs
import hashlib
import StringIO
from datetime import datetime

import utils
import settings
from models import *
from database import db_session, init_db

def initdb():
    key = int(time.time()) // 60
    key = hashlib.md5(str(key)).hexdigest()[:6]
    if len(sys.argv) != 3 or sys.argv[2] != key:
        print('please run the following command within the current minute')
        print('    ./maintenance.py initdb %s' % key)
        sys.exit(1)
    print('initializing the database')
    init_db()
    print('done!')


def add_compiler():
    if len(sys.argv) != 4:
        print('usage: ./maintenance.py add_compiler <student> <repo_url>')
        sys.exit(1)
    student = sys.argv[2].decode('utf-8')
    repo_url = sys.argv[3]
    c = Compiler(student=student, repo_url=repo_url)
    db_session.add(c)
    db_session.commit()
    print('done!')


def add_testcase():
    if len(sys.argv) not in [3, 4]:
        print('usage: ./maintenance.py add_testcase <path_to_testcase> [-y]')
        sys.exit(1)
    with codecs.open(sys.argv[2], 'r', 'utf-8') as f:
        content = f.read()
    t = utils.parse_testcase(content)
    if len(sys.argv) == 4:
        assert sys.argv[3] == '-y'
    else:
        print(utils.testcase_to_text(t))
        confirm = raw_input('Confirm (y/n)? ')
        assert confirm.strip() == 'y'
    testcase = Testcase(enabled=True,
                        phase=t['phase'],
                        is_public=t['is_public'],
                        comment=t['comment'],
                        timeout=t.get('timeout', None),
                        cnt_run=0,
                        cnt_hack=0,
                        content=json.dumps(t))
    db_session.add(testcase)
    db_session.commit()

    tphase = utils.phase_to_index(testcase.phase)
    for compiler in db_session.query(Compiler):
        version = db_session.query(Version).filter(Version.id == compiler.latest_version_id).one()
        vphase = utils.phase_to_index(version.phase)
        if vphase > tphase or (vphase == tphase and version.status != 'pending'):
            r = TestRun(version_id=version.id,
                        testcase_id=testcase.id,
                        phase=testcase.phase,
                        status='pending',
                        created_at=datetime.utcnow())
            db_session.add(r)
            version.phase = testcase.phase
            version.status = 'running'
    db_session.commit()
    print('done!', sys.argv[2])


def set_testcase():
    if len(sys.argv) != 4:
        print('usage: ./maintenance.py set_testcase <testcase_id> enable/disable')
        sys.exit(1)
    testcase_id = int(sys.argv[2])
    assert sys.argv[3] in ['enable', 'disable']
    enabled = sys.argv[3] == 'enable'
    t = db_session.query(Testcase).filter(Testcase.id == testcase_id).one()
    t.enabled = enabled
    db_session.commit()
    print('done!')


def rejudge_version():
    if len(sys.argv) != 3:
        print('usage: ./maintenance.py rejudge_version <version_id>')
        sys.exit(1)
    version_id = int(sys.argv[2])
    old = db_session.query(Version).filter(Version.id == version_id).one()
    compiler = db_session.query(Compiler).filter(Compiler.id == old.compiler_id).one()
    new = Version(compiler_id=old.compiler_id,
                  sha=old.sha,
                  phase='build',
                  status='pending')
    db_session.add(new)
    db_session.commit()
    compiler.latest_version_id = new.id
    db_session.commit()
    print('done! the new version_id is', new.id)


def clear_judge_testcase_cache():
    os.system('rm {}/*'.format(settings.JUDGE_TESTCASE_PATH))


def makedirs():
    def mkdir(path):
        if not os.path.exists(path):
            os.makedirs(path)
    mkdir(settings.CORE_BUILD_LOG_PATH)
    mkdir(settings.CORE_TESTRUN_STDERR_PATH)
    mkdir(settings.JUDGE_GIT_REPO_PATH)
    mkdir(settings.JUDGE_TESTCASE_PATH)
    print('done!')


if __name__ == '__main__':
    actions = [
	add_compiler,
	add_testcase,
	set_testcase,
	rejudge_version,
        initdb,
	makedirs,
	clear_judge_testcase_cache,
    ]
    action_map = {func.__name__: func for func in actions}
    if len(sys.argv) < 2 or sys.argv[1] not in action_map:
        print('usage: ./maintenance.py <action>')
        print('<action> can be:')
        for k in actions:
            print('    %s' % k.__name__)
        sys.exit(1)
    action_map[sys.argv[1]]()
