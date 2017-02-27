import time

from .. import settings
from ..database import db_session
from ..models import *

def do_pending(version):
    version.status = 'running'
    testcases = db_session.query(Testcase).filter(enabled=True, phase=version.phase)
    for testcase in testcases:
        r = TestRun(version_id=version.id,
                    testcase_id=testcase.id,
                    phase=version.phase,
                    status='pending',
                    created_at=datetime.utcnow())
        db_session.add(r)
    db_session.commit()


def watch_testrun_running(phase, is_pretest):
    query_base = db_session.query(func.count(TestRun.id))
                           .filter(TestRun.version_id == r.version_id)
                           .filter(TestRun.phase == r.phase)
    total = query_base.scalar()
    success = query_base.filter(TestRun.status == 'ok').scalar()
    failure = query_base.filter(TestRun.status == 'failed').scalar()

    if success + failure == total:
        if success == total:
            idx = settings.TEST_PHASES.index(phase)
            if idx == len(settings.TEST_PHASES) - 1:
                version.phase = 'end'
                version.status = 'passed'
            else:
                version.phase = settings.TEST_PHASES[idx+1]
                version.status = 'pending'
        else:
            version.status = 'failed'
    db_session.commit()


def watch():
    while True:
        handler = {'running': do_running, 'pending': do_pending}
        versions = db_session.query(Version)
                             .filter(Version.status.in_(handler.keys()))
                             .order_by(Version.id.asc())
        for version in versions:
            if version.phase in settings.TEST_PHASES:
                handler[version.status](version)
        time.sleep(1)
