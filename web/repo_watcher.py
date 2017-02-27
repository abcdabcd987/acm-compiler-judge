import time
import subprocess

from .. import settings
from ..database import db_session
from ..models import *

def get_latest_remote_version(repo_url):
    cmd = 'git ls-remote {} master | cut -f1'.format(repo_url)
    try:
        version = subprocess.check_output(cmd, shell=True)
    except:
        return False
    if len(version) != 40:
        return False
    return version


def do_compiler():
    version_sha = get_latest_remote_version(compiler.repo_url)
    newer = False
    if compiler.latest_version_id:
        version = db_session.query(Version)
                            .filter(Version.id == compiler.latest_version_id)
                            .one()
        if version_sha != version.sha:
            newer = True
    else:
        newer = True
    if newer:
        version = Version(compiler_id=compiler.id,
                          sha=version_sha,
                          phase='build',
                          status='pending')
        db_session.add(version)
        db_session.commit()


def watch():
    while True:
        compilers = db_session.query(Compiler)
        for compiler in compilers:
            do_compiler(compiler)
        time.sleep(1)
