#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
import os
import sys
import hashlib
import StringIO
from datetime import datetime

import utils
from models import *
from database import db_session, init_db

def initdb():
    key = int(time.time()) // 60
    key = hashlib.md5(str(key)).hexdigest()[:6]
    if len(sys.argv) != 3 or sys.argv[2] != key:
        print('please run the following command within the current minute')
        print('    python maintenance.py initdb %s' % key)
        sys.exit(1)
    print('initializing the database')
    init_db()
    print('done!')


def add_compiler():
    if len(sys.argv) != 4:
        print('usage: ./maintenance.py add_compiler <student> <repo_url>')
        sys.exit(1)
    student = sys.argv[2]
    repo_url = sys.argv[3]
    c = Compiler(student=student, repo_url=repo_url)
    db_session.add(c)
    db_session.commit()
    print('done!')


def add_testcase():
    end_token = 'END'
    def read_until_end(prompt):
        sio = StringIO.StringIO()
        print(prompt, '(END to mark the end):')
        while True:
            line = raw_input()
            if line == end_token:
                break
            print(line, file=sio)
        return sio.getvalue()
    
    t = {}
    t['program'] = read_until_end('program')
    asserts = ['success_exit', 'failure_exit', 'exitcode', 'output']
    t['assert'] = raw_input('assert ({}): '.format(' / '.join(asserts)))
    assert t['assert'] in asserts
    if t['assert'] == 'exitcode':
        t['exitcode'] = int(raw_input('exitcode (0~255): '))
        assert 0 <= t['exitcode'] <= 255
    elif t['assert'] == 'output':
        t['output'] = read_until_end('output')
    t['input'] = read_until_end('input')
    t['phase'] = raw_input('phase ({}): '.format(' / '.join(settings.TEST_PHASES))).strip()
    assert t['phase'] in settings.TEST_PHASES
    t['comment'] = read_until_end('comment')
    is_public = raw_input('is public? (y/n): ')
    assert is_public in ['y', 'n']
    t['is_public'] = is_public == 'y'        

    text = utils.testcase_to_text(t)
    print(text)
    yes = raw_input('confirm? (y/n): ')
    assert yes == 'y'

    testcase = Testcase(enabled=True,
                        phase=t['phase'],
                        is_public=t['is_public'],
                        comment=t['comment'],
                        content=json.dumps(t))
    db_session.add(testcase)
    db_session.commit()
    print('done!')


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


if __name__ == '__main__':
    actions = [initdb, add_compiler, add_testcase, set_testcase]
    action_map = {func.__name__: func for func in actions}
    if len(sys.argv) < 2 or sys.argv[1] not in action_map:
        print('usage: ./maintenance.py <action>')
        print('<action> can be:')
        for k in action_map:
            print('    %s' % k)
        sys.exit(1)
    action_map[sys.argv[1]]()
