#!/usr/bin/env python
import os
import sys
import time
from datetime import datetime
from sqlalchemy import func

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
import settings
from database import db_session
from models import *


def do_pending(version):
    print 'add testrun for version {0.id}, phase {0.phase}, status {0.status}'.format(version)
    query = db_session.query(TestRun)\
                      .filter(TestRun.version_id == version.id)\
                      .filter(TestRun.phase == version.phase)
    presented = set(r.testcase_id for r in query)

    testcases = db_session.query(Testcase)\
                          .filter(Testcase.enabled == True)\
                          .filter(Testcase.phase == version.phase)
    for testcase in testcases:
        if testcase.id not in presented:
            r = TestRun(version_id=version.id,
                        testcase_id=testcase.id,
                        phase=testcase.phase,
                        status='pending',
                        created_at=datetime.utcnow())
            db_session.add(r)
    version.status = 'running'
    db_session.commit()


def do_running(version):
    query_base = db_session.query(func.count(TestRun.id))\
                           .filter(TestRun.version_id == version.id)\
                           .filter(TestRun.phase == version.phase)
    total = query_base.scalar()
    success = query_base.filter(TestRun.status == 'passed').scalar()
    failure = query_base.filter(~TestRun.status.in_(['pending', 'running', 'passed'])).scalar()

    if success + failure == total:
        print 'set next phase for version {0.id}, phase {0.phase}, status {0.status}'.format(version)
        if success == total:
            idx = settings.TEST_PHASES.index(version.phase)
            if idx == len(settings.TEST_PHASES) - 1:
                version.phase = 'end'
                version.status = 'passed'
            else:
                version.phase = settings.TEST_PHASES[idx+1]
                version.status = 'pending'
        else:
            version.status = 'failed'
        db_session.commit()


def main():
    print 'testrun_watcher started'
    while True:
        handler = {'running': do_running, 'pending': do_pending}
        versions = db_session.query(Version)\
                             .filter(Version.status.in_(handler.keys()))\
                             .order_by(Version.id.asc())
        for version in versions:
            if version.phase in settings.TEST_PHASES:
                handler[version.status](version)
        db_session.commit()
        time.sleep(1)


if __name__ == '__main__':
    main()
