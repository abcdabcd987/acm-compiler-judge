#!/usr/bin/env python
import os
import sys
import time
import json
import shutil
import codecs
import random
import requests
import tempfile
import subprocess
import StringIO
from pprint import pprint

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
import settings, utils

null = open(os.devnull, 'w')

def ensure_testcase(testcase_id):
    path = os.path.join(settings.JUDGE_TESTCASE_PATH, '{:d}.json'.format(testcase_id))
    if not os.path.exists(path):
        print ' downloading testcase', testcase_id
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
        print ' testcase downloaded'
    with open(path) as f:
        return json.loads(f.read())


def clone_repo(compiler):
    repo_root = os.path.join(settings.JUDGE_GIT_REPO_PATH, str(compiler['id']))
    if not os.path.exists(repo_root):
        subprocess.check_call(['git', 'clone', compiler['repo_url'], repo_root], stdout=null, stderr=null)


def pull_repo(compiler):
    repo_root = os.path.join(settings.JUDGE_GIT_REPO_PATH, str(compiler['id']))
    subprocess.check_call(['git', 'fetch', 'origin', 'master'], cwd=repo_root, stdout=null, stderr=null)
    subprocess.check_call(['git', 'reset', '--hard', 'FETCH_HEAD'], cwd=repo_root, stdout=null, stderr=null)
    subprocess.check_call(['git', 'clean', '-df'], cwd=repo_root, stdout=null, stderr=null)


def checkout_repo(version, target):
    repo_root = os.path.join(settings.JUDGE_GIT_REPO_PATH, str(version['compiler_id']))
    subprocess.check_call(['git', 'checkout', version['sha']], cwd=repo_root, stdout=null, stderr=null)
    subprocess.check_call('git archive {} | tar -x -C {}'.format(version['sha'], target), shell=True, cwd=repo_root, stdout=null, stderr=null)
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
    print ' building docker image for version', version['id']
    clone_repo(compiler)
    print '  git clone done'
    pull_repo(compiler)
    print '  git pull done'
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
    print '  docker build starts'
    tic = time.time()
    try:
        log = subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=root)
        ok = True
    except subprocess.CalledProcessError as e:
        log = e.output
        ok = False
    toc = time.time()
    print '  docker build finished, ok = ', ok
    shutil.rmtree(root)
    log = log[:settings.LOG_LENGTH_LIMIT]
    print ' image build finished'
    return commit_date, comment, ok, log, toc-tic


def build_and_send_log(version, compiler):
    commit_date, comment, ok, log, build_time = build_docker_image(version, compiler)
    print ' submitting build result'
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
    while True:
        try:
            r = requests.post(url, data=data, timeout=settings.JUDGE_REQUEST_TIMEOUT)
            r.raise_for_status()
            break
        except:
            print 'failed to post build_log for version {:d}'.format(version['id'])
            time.sleep(1)
    print ' submitted'
    return ok


def do_build():
    url = settings.CORE_URL + '/backend/dispatch/build'
    data = {'token': settings.JUDGE_TOKEN, 'judge': settings.JUDGE_NAME}
    try:
        r = requests.post(url, data=data, timeout=settings.JUDGE_REQUEST_TIMEOUT)
        resp = r.json()
    except:
        print 'failed to fetch build tasks'
        return False
    if not resp['found']:
        return False
    version, compiler = resp['version'], resp['compiler']
    print 'got a build task for version', version['id']
    build_and_send_log(version, compiler)
    print 'build task done\n'
    return True


def judge_testcase(testcase, exitcode, stdout):
    if testcase['assert'] == 'exitcode':
        return exitcode == testcase['exitcode']
    if testcase['assert'] == 'runtime_error':
        return exitcode != 0
    if testcase['assert'] == 'output':
        if exitcode != 0:
            return False
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


def run(compiler, version, testcase, testrun, command, runner_code, asm_code=None):
    print ' run', command
    root = tempfile.mkdtemp(prefix='acm-compiler-judge-testrun')
    cmd = ['docker', 'run', '-d']
    cmd += ['-m', settings.JUDGE_RUN_MEMORY_LIMIT]
    cmd += ['-v', '{}:/testrun'.format(root), '{}:{}'.format(compiler['id'], version['id'])]
    cmd += ['bash', '/testrun/runner.bash']
    with open(os.path.join(root, 'runner.bash'), 'w') as f:
        f.write(runner_code)
    if command == 'run':
        with open(os.path.join(root, 'input.txt'), 'w') as f:
            f.write(testcase['input'])
        with open(os.path.join(root, 'program.asm'), 'w') as f:
            f.write(asm_code)
        cmd += ['/testrun/program.asm', '/testrun/input.txt']
    else:
        with codecs.open(os.path.join(root, 'program.txt'), 'w', 'utf-8') as f:
            f.write(testcase['program'])
        phase_prefix = testrun['phase'].split()[0]
        cmd += [phase_prefix, '/testrun/testcase.txt']

    print '  docker container starting'
    docker_id = subprocess.check_output(cmd).strip()
    print '  docker container id', docker_id

    is_timeout = True
    time_lim = testcase['timeout'] if command == 'run' else settings.JUDGE_COMPILE_TIMEOUT
    timeout = time_lim + 3
    st = time.time()
    while time.time() - st < timeout:
        log = subprocess.check_output(['docker', 'ps', '-q', '--filter', 'id={}'.format(docker_id)])
        if log.strip() == '':
            is_timeout = False
            break
    subprocess.call(['docker', 'kill', docker_id], stdout=null, stderr=null)
    subprocess.check_call(['docker', 'rm', docker_id], stdout=null, stderr=null)
    print '  docker container killed & removed'
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
        time_sec = time_lim
    if is_timeout:
        time_sec = time_lim
    shutil.rmtree(root)
    print ' run finished'
    return exitcode, stdout, stderr, time_sec


def do_testrun():
    global code_runner_compile, code_runner_run
    url = settings.CORE_URL + '/backend/dispatch/testrun'
    data = {'token': settings.JUDGE_TOKEN, 'judge': settings.JUDGE_NAME}
    try:
        r = requests.post(url, data=data, timeout=settings.JUDGE_REQUEST_TIMEOUT)
        resp = r.json()
    except:
        print 'failed to fetch testrun tasks'
        return False
    if not resp['found']:
        return False
    testrun, version, compiler = resp['testrun'], resp['version'], resp['compiler']
    print 'got a run task for testrun', testrun['id']

    if not check_docker_image_exist(version, compiler):
        ok = build_and_send_log(version, compiler)
        assert ok
    testcase = ensure_testcase(testrun['testcase_id'])

    results = []
    exitcode, asm_code, stderr, time_sec = run(compiler, version, testcase, testrun, 'compile', code_runner_compile)
    compile_time = time_sec
    if time_sec >= settings.JUDGE_COMPILE_TIMEOUT:
        final_status = 'timeout'
        results.append(('compile', exitcode, stderr, time_sec, final_status))
    elif testcase['assert'] == 'failure_compile':
        final_status = 'passed' if exitcode != 0 else 'failed'
        results.append(('compile', exitcode, stderr, time_sec, final_status))
    elif testcase['assert'] == 'success_compile':
        final_status = 'passed' if exitcode == 0 else 'failed'
        results.append(('compile', exitcode, stderr, time_sec, final_status))
    elif exitcode != 0:
        final_status = 'failed'
        results.append(('compile', exitcode, stderr, time_sec, final_status))
    else:
        final_status = 'passed'
        results.append(('compile', exitcode, stderr, time_sec, final_status))
        for i in xrange(settings.JUDGE_RUN_TIMES_PER_TEST):
            exitcode, stdout, stderr, time_sec = run(compiler, version, testcase, testrun, 'run', code_runner_run, asm_code)
            if time_sec >= testcase['timeout']:
                status = 'timeout'
            else:
                ok = judge_testcase(testcase, exitcode, stdout)
                status = 'passed' if ok else 'failed'
            results.append(('run{:4d}'.format(i+1), exitcode, stderr, time_sec, status))
            if status == 'failed':
                final_status = status
                break
    if len(results) > 1:
        times = []
        for name, exitcode, stderr, time_sec, status in results[1:]:
            times.append(time_sec)
        running_time = sum(times) / len(times)
        if running_time >= testcase['timeout']:
            final_status = 'timeout'
    else:
        running_time = .0

    print ' formating log'
    sio = StringIO.StringIO()
    sio.write('=== compile & run info ===\n')
    for name, exitcode, stderr, time_sec, status in results:
        sio.write('{}: exitcode {:3d} | time {:6.3f}s | {}\n'.format(name, exitcode, time_sec, status))
    for name, exitcode, stderr, time_sec, status in results:
        sio.write('\n\n=== stderr of {} ===\n'.format(name))
        sio.write(stderr)
    print ' log formatted'

    print ' submitting run result'
    url = settings.CORE_URL + '/backend/submit/testrun'
    data = {
        'token': settings.JUDGE_TOKEN,
        'judge': settings.JUDGE_NAME,
        'id': testrun['id'],
        'running_time': running_time,
        'compile_time': compile_time,
        'status': final_status,
        'stderr': sio.getvalue()
    }
    while True:
        try:
            r = requests.post(url, data=data, timeout=settings.JUDGE_REQUEST_TIMEOUT)
            r.raise_for_status()
            break
        except:
            print 'failed to post build_log for version {:d}'.format(version['id'])
            time.sleep(1)
    print ' submitted'
    print 'task done\n'
    return True


if __name__ == '__main__':
    global code_runner_compile, code_runner_run
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'runner_compile.bash')) as f:
        code_runner_compile = f.read()
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'runner_run.bash')) as f:
        code_runner_run = f.read()
    while True:
        done1 = do_build() if random.random() < 0.05 else False
        done2 = do_testrun()
        if not done1 and not done2:
            time.sleep(1)
