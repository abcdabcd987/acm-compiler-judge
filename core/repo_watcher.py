#!/usr/bin/env python
import os
import sys
import time
import subprocess
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
import settings
from database import db_session
from models import *

def get_latest_remote_version(repo_url):
    cmd = 'git ls-remote {} master | grep refs/heads/master | cut -f1'.format(repo_url)
    try:
        version = subprocess.check_output(cmd, shell=True).strip()
    except:
        return False
    if len(version) != 40:
        return False
    return version


def do_compiler(compiler):
    version_sha = get_latest_remote_version(compiler.repo_url)
    compiler.last_check_time = datetime.utcnow()
    db_session.commit()
    if not version_sha:
        return
    newer = False
    if compiler.latest_version_id:
        version = db_session.query(Version)\
                            .filter(Version.id == compiler.latest_version_id)\
                            .one()
        if version_sha != version.sha:
            newer = True
    else:
        newer = True
    if newer:
        print "add %s's version %s" % (compiler.student, version_sha)
        version = Version(compiler_id=compiler.id,
                          sha=version_sha,
                          phase='build',
                          status='pending')
        db_session.add(version)
        db_session.commit()
        compiler.latest_version_id = version.id
        db_session.commit()


def main():
    print 'repo_watcher started'
    compilers = db_session.query(Compiler).all()
    while True:
        for compiler in compilers:
            do_compiler(compiler)
            time.sleep(2)


if __name__ == '__main__':
    main()
