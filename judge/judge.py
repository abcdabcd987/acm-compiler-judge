#!/usr/bin/env python
import os
import sys
import time
import json
import shutil
import requests
import tempfile
import subprocess
from pprint import pprint

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
import settings, utils

def ensure_testcase(testcase_id):
    path = os.path.join(settings.JUDGE_TESTCASE_PATH, '{:d}.json'.format(testcase_id))
    if not os.path.exists(path):
        url = settings.CORE_URL + '/backend/download/testcase/{:d}.json'.format(testcase_id)
        data = {'token': settings.JUDGE_TOKEN}
        while True:
            try:
                r = requests.post(url, data=data)
                r.raise_for_status()
                content = r.content
                break
            except:
                print 'failed to download testcase {}'.format(testcase_id)
                time.sleep(1)
        with open(path, 'w') as f:
            f.write(content)
    with open(path) as f:
        return json.loads(f.read())


def clone_repo(compiler):
    repo_root = os.path.join(settings.JUDGE_GIT_REPO_PATH, str(compiler['id']))
    if not os.path.exists(repo_root):
        subprocess.check_call(['git', 'clone', compiler['repo_url'], repo_root])


def pull_repo(compiler):
    repo_root = os.path.join(settings.JUDGE_GIT_REPO_PATH, str(compiler['id']))
    subprocess.check_call(['git', 'fetch', 'origin', 'master'], cwd=repo_root)
    subprocess.check_call(['git', 'reset', '--hard', 'FETCH_HEAD'], cwd=repo_root)
    subprocess.check_call(['git', 'clean', '-df'], cwd=repo_root)


def checkout_repo(version, target):
    repo_root = os.path.join(settings.JUDGE_GIT_REPO_PATH, str(version['compiler_id']))
    subprocess.check_call(['git', 'checkout', version['sha']], cwd=repo_root)
    subprocess.check_call('git archive {} | tar -x -C {}'.format(version['sha'], target), shell=True, cwd=repo_root)
    formats = '\x1f'.join(['%ad', '%s\n%b'])
    cmd = ['git', 'log', '-n', '1', '--format={}'.format(formats), version['sha']]
    log = subprocess.check_output(cmd, cwd=repo_root).strip()
    date, comment = log.split('\x1f')
    return date, comment


def check_docker_image_exist(version, compiler):
    cmd = ['docker', 'images', '-q', '{}:{}'.format(compiler['id'], version['id'])]
    out = subprocess.check_output(cmd).strip()
    return out != ''


def build_docker_image(version, compiler):
    clone_repo(compiler)
    pull_repo(compiler)
    root = tempfile.mkdtemp(prefix='acm-compiler-judge-build')
    root_compiler = os.path.join(root, 'compiler')
    os.mkdir(root_compiler)
    commit_date, comment = checkout_repo(version, root_compiler)
    with open(os.path.join(root, 'Dockerfile'), 'w') as f:
        f.write('''
FROM acm-compiler-judge
ADD compiler /compiler
WORKDIR /compiler
RUN bash /compiler/build.bash
''')
    cmd = ['timeout', '{}s'.format(settings.JUDGE_BUILD_TIMEOUT)]
    cmd += ['docker', 'build', '-t={}:{}'.format(compiler['id'], version['id']), '.']
    tic = time.time()
    try:
        log = subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=root)
        ok = True
    except subprocess.CalledProcessError as e:
        log = e.output
        ok = False
    toc = time.time()
    shutil.rmtree(root)
    log = log[:settings.LOG_LENGTH_LIMIT]
    return commit_date, comment, ok, log, toc-tic


def build_and_send_log(version, compiler):
    commit_date, comment, ok, log, build_time = build_docker_image(version, compiler)
    url = settings.CORE_URL + '/backend/submit/build_log'
    data = {
        'token': settings.JUDGE_TOKEN,
        'judge': settings.JUDGE_NAME,
        'id': str(version['id']),
        'message': comment,
        'committed_at': commit_date,
        'status': 'ok' if ok else 'failed',
        'build_time': str(build_time),
        'log': log
    }
    pprint(data)
    while True:
        try:
            r = requests.post(url, data=data, timeout=settings.JUDGE_REQUEST_TIMEOUT)
            r.raise_for_status()
            break
        except:
            print 'failed to post build_log for version {:d}'.format(version['id'])
            time.sleep(1)
    return ok


def do_build():
    url = settings.CORE_URL + '/backend/dispatch/build'
    data = {'token': settings.JUDGE_TOKEN, 'judge': settings.JUDGE_NAME}
    try:
        r = requests.post(url, data=data, timeout=settings.JUDGE_REQUEST_TIMEOUT)
        resp = r.json()
    except:
        print 'failed to fetch build tasks'
        return
    if not resp['found']:
        return
    version, compiler = resp['version'], resp['compiler']
    build_and_send_log(version, compiler)


def judge_testcase(testcase, exitcode, stdout):
    if testcase['assert'] == 'success_exit':
        return exitcode == 0
    if testcase['assert'] == 'failure_exit':
        return exitcode != 0
    if testcase['assert'] == 'exitcode':
        return exitcode == testcase['exitcode']
    if testcase['assert'] == 'output':
        out_lines = stdout.strip().splitlines()
        ans_lines = testcase['output'].strip().splitlines()
        if len(out_lines) != len(ans_lines):
            return False
        for out_line, ans_line in zip(out_lines, ans_lines):
            if out_line.strip() != ans_line.strip():
                return False
        return True
    print 'unknown assertion', testcase['assert']
    assert False


def do_testrun():
    url = settings.CORE_URL + '/backend/dispatch/testrun'
    data = {'token': settings.JUDGE_TOKEN, 'judge': settings.JUDGE_NAME}
    try:
        r = requests.post(url, data=data, timeout=settings.JUDGE_REQUEST_TIMEOUT)
        resp = r.json()
    except:
        print 'failed to fetch testrun tasks'
        return
    if not resp['found']:
        return
    testrun, version, compiler = resp['testrun'], resp['version'], resp['compiler']

    if not check_docker_image_exist(version, compiler):
        ok = build_and_send_log(version, compiler)
        assert ok
    testcase = ensure_testcase(testrun['testcase_id'])
    root = tempfile.mkdtemp(prefix='acm-compiler-judge-testrun')
    with open(os.path.join(root, 'testcase.txt'), 'w') as f:
        f.write(testcase['program'])
    with open(os.path.join(root, 'runner.bash'), 'w') as f:
        f.write('''
cd /compiler
st=$(date +%s%N)
"$@" 1> /testrun/stdout.txt 2> /testrun/stderr.txt
echo $? > /testrun/exitcode.txt
ed=$((($(date +%s%N) - $st)/1000))
echo "$ed" > /testrun/time_us.txt
''')
    cmd = ['docker', 'run', '-d', '-v', '{}:/testrun'.format(root), '{}:{}'.format(compiler['id'], version['id'])]
    cmd += ['bash', '/testrun/runner.bash', 'bash', '/compiler/{}.bash'.format(testrun['phase'].split()[0]), '/testrun/testcase.txt']
    if 'input' in testcase:
        with open(os.path.join(root, 'input.txt'), 'w') as f:
            f.write(testcase['input'])
        cmd += ['/testrun/input.txt']
    docker_id = subprocess.check_output(cmd).strip()
    is_timeout = True
    timeout = int(testcase['timeout']+1)
    st = time.time()
    while time.time() - st < timeout:
        log = subprocess.check_output(['docker', 'ps', '-q', '--filter', 'id={}'.format(docker_id)])
        if log.strip() == '':
            is_timeout = False
            break
    subprocess.call(['docker', 'kill', docker_id])
    subprocess.check_call(['docker', 'rm', docker_id])
    try:
        with open(os.path.join(root, 'stdout.txt')) as f:
            stdout = f.read()
    except:
        stdout = ''
    try:
        with open(os.path.join(root, 'stderr.txt')) as f:
            stderr = f.read()[:settings.LOG_LENGTH_LIMIT]
    except:
        stderr = ''
    try:
        with open(os.path.join(root, 'exitcode.txt')) as f:
            exitcode = int(f.read())
    except:
        exitcode = -1
    try:
        with open(os.path.join(root, 'time_us.txt')) as f:
            time_us = f.read().strip()
            time_sec = float(time_us) / 1e6
    except:
        time_sec = testcase['timeout']
    shutil.rmtree(root)
    if is_timeout or time_sec >= testcase['timeout']:
        status = 'timeout'
    else:
        ok = judge_testcase(testcase, exitcode, stdout)
        status = 'passed' if ok else 'failed'
    
    url = settings.CORE_URL + '/backend/submit/testrun'
    data = {
        'token': settings.JUDGE_TOKEN,
        'judge': settings.JUDGE_NAME,
        'id': testrun['id'],
        'running_time': time_sec,
        'status': status,
        'stderr': stderr
    }
    pprint(data)
    while True:
        try:
            r = requests.post(url, data=data, timeout=settings.JUDGE_REQUEST_TIMEOUT)
            r.raise_for_status()
            break
        except:
            print 'failed to post build_log for version {:d}'.format(version['id'])
            time.sleep(1)


if __name__ == '__main__':
    while True:
        do_build()
        do_testrun()
        time.sleep(1)
