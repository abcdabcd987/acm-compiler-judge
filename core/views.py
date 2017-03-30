# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import uuid
import json
import functools
import StringIO
from datetime import datetime
from collections import namedtuple
from ansi2html import ansi2html
from flask import request, redirect, session, url_for, flash, render_template, jsonify, abort, send_file, Response

from web import app
from models import *
from database import db_session
import settings, utils

JudgeStatus = namedtuple('JudgeStatus', ['name', 'action', 'time'])
judge_status = {}

def copy_sqlalchemy_object_as_dict(o):
    d = dict(o.__dict__)
    del d['_sa_instance_state']
    return d


@app.route(settings.WEBROOT + '/')
def homepage():
    return render_template('homepage.html')


@app.route(settings.WEBROOT + '/compilers/')
def compilers():
    compilers = db_session.query(Compiler).order_by(Compiler.id.asc()).all()
    versions = []
    for c in compilers:
        if c.latest_version_id:
            v = db_session.query(Version).filter(Version.id == c.latest_version_id).one()
        else:
            v = None
        versions.append(v)
    return render_template('compilers.html', compilers=compilers, versions=versions)


def get_verion_testrun_counts(version):
    passed = {k: 0 for k in settings.TEST_PHASES}
    total = {k: 0 for k in settings.TEST_PHASES}
    for r in db_session.query(TestRun).filter(TestRun.version_id == version.id):
        total[r.phase] += 1
        if r.status == 'passed':
            passed[r.phase] += 1
    ret = {p: (passed[p], total[p]) if total[p] else None for p in settings.TEST_PHASES}
    ret['build'] = 'passed' if version.phase != 'build' else version.status
    return ret


@app.route(settings.WEBROOT + '/builds')
def builds():
    try: start = int(request.args['start'])
    except: start = ''
    try: compiler_id = int(request.args['compiler_id'])
    except: compiler_id = ''
    sha = request.args.get('sha', '')
    phase = request.args.get('phase', '')
    status = request.args.get('status', '')

    query = db_session.query(Version).order_by(Version.id.desc())
    if compiler_id: query = query.filter(Version.compiler_id == compiler_id)
    if sha: query = query.filter(Version.sha.like(sha + '%'))
    if phase: query = query.filter(Version.phase == phase)
    if status: query = query.filter(Version.status == status)
    if start: query = query.filter(Version.id <= start)
    query = query.limit(settings.BUILDS_PER_PAGE)
    versions = query.all()
    counts = [get_verion_testrun_counts(v) for v in versions]
    cs = {c.id: c for c in db_session.query(Compiler)}
    return render_template('builds.html', versions=versions, compilers=cs, counts=counts)


@app.route(settings.WEBROOT + '/runs')
def runs():
    try: start = int(request.args['start'])
    except: start = ''
    try: version_id = int(request.args['build_id'])
    except: version_id = ''
    try: testcase_id = int(request.args['testcase_id'])
    except: testcase_id = ''
    phase = request.args.get('phase', '')
    status = request.args.get('status', '')

    query = db_session.query(TestRun).order_by(TestRun.id.desc())
    auto_refresh = not (version_id or testcase_id or phase or status or start)
    if version_id: query = query.filter(TestRun.version_id == version_id)
    if testcase_id: query = query.filter(TestRun.testcase_id == testcase_id)
    if phase: query = query.filter(TestRun.phase == phase)
    if status: query = query.filter(TestRun.status == status)
    if start: query = query.filter(TestRun.id <= start)
    query = query.limit(settings.RUNS_PER_PAGE)
    rs = query.all()
    vids = set(r.version_id for r in rs)
    vs = {v.id: v for v in db_session.query(Version).filter(Version.id.in_(vids))}
    cs = {c.id: c for c in db_session.query(Compiler)}
    ts = {t.id: t for t in db_session.query(Testcase)}
    watch_list = [r.id for r in rs if r.status not in ['passed', 'failed', 'timeout']]
    return render_template('runs.html', testruns=rs, testcases=ts, compilers=cs, versions=vs,
        auto_refresh=auto_refresh, watch_list=watch_list)


@app.route(settings.WEBROOT + '/ajax/watch_runs.json')
def ajax_watch_runs():
    try:
        lim = 10
        stamp = int(request.args['stamp'])
        qs = request.args.get('q', '').strip()
        qs = map(lambda q: int(q.strip()), qs.split(',')) if qs else []
        qs = sorted(qs)[:lim]
        old = []
        for testrun_id in qs:
            r = db_session.query(TestRun).filter(TestRun.id == testrun_id).one()
            v = db_session.query(Version).filter(Version.id == r.version_id).one()
            c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
            t = db_session.query(Testcase).filter(Testcase.id == r.testcase_id).one()
            old.append({
                'id': r.id,
                'row_html': render_template('runs_row.html', r=r, v=v, c=c, t=t),
                'finished': r.status in ['passed', 'failed', 'timeout'],
            })

        try: latest_id = int(request.args['latest_id'])
        except: latest_id = 1<<30
        query = db_session.query(TestRun).filter(TestRun.id > latest_id)\
                          .order_by(TestRun.id.asc()).limit(lim)
        new = []
        for r in query:
            v = db_session.query(Version).filter(Version.id == r.version_id).one()
            c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
            t = db_session.query(Testcase).filter(Testcase.id == r.testcase_id).one()
            new.append({
                'id': r.id,
                'row_html': render_template('runs_row.html', r=r, v=v, c=c, t=t),
                'finished': r.status in ['passed', 'failed', 'timeout'],
            })
        return jsonify({'watch': old, 'new': new, 'stamp': stamp})
    except:
        return abort(400)


@app.route(settings.WEBROOT + '/testcases')
def testcases():
    ts = db_session.query(Testcase).order_by(Testcase.id.desc()).all()
    return render_template('testcases.html', testcases=ts)


def get_build_phase_count(rs):
    count = { phase: dict() for phase in settings.TEST_PHASES }
    for r in rs:
        d = count[r.phase]
        d[r.status] = d.get(r.status, 0) + 1
        d['total'] = d.get('total', 0) + 1
    return count


@app.route(settings.WEBROOT + '/build/<int:id>')
def build(id):
    v = db_session.query(Version).filter(Version.id == id).first()
    if not v:
        return abort(404)
    c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
    ls = db_session.query(BuildLog).filter(BuildLog.version_id == id).order_by(BuildLog.id.desc()).all()
    rs = db_session.query(TestRun).filter(TestRun.version_id == id).order_by(TestRun.id.desc()).all()
    ts = {t.id: t for t in db_session.query(Testcase)}
    count = get_build_phase_count(rs)
    watch_list = [r.id for r in rs if r.status not in ['passed', 'failed', 'timeout']]
    auto_refresh = v.status not in ['passed', 'failed']
    return render_template('build.html', compiler=c, version=v, build_logs=ls, 
        testruns=rs, testcases=ts, phase_count=count, auto_refresh=auto_refresh,
        watch_list=watch_list)


@app.route(settings.WEBROOT + '/ajax/build.json')
def ajax_build():
    try:
        stamp = int(request.args['stamp'])
        latest_id = int(request.args['latest_id'])
        id = int(request.args['build_id'])
        v = db_session.query(Version).filter(Version.id == id).first()
        if not v:
            return abort(404)

        lim = 10
        stamp = int(request.args['stamp'])
        qs = request.args.get('q', '').strip()
        qs = map(lambda q: int(q.strip()), qs.split(',')) if qs else []
        qs = sorted(qs)[:lim]
        watch = []
        for testrun_id in qs:
            r = db_session.query(TestRun).filter(TestRun.id == testrun_id).one()
            v = db_session.query(Version).filter(Version.id == r.version_id).one()
            c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
            t = db_session.query(Testcase).filter(Testcase.id == r.testcase_id).one()
            watch.append({
                'id': r.id,
                'row_html': render_template('build_row.html', r=r, v=v, c=c, t=t),
                'finished': r.status in ['passed', 'failed', 'timeout'],
            })

        c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
        ls = db_session.query(BuildLog).filter(BuildLog.version_id == id).order_by(BuildLog.id.desc()).all()
        rs = db_session.query(TestRun).filter(TestRun.version_id == id).order_by(TestRun.id.asc()).all()
        ts = {t.id: t for t in db_session.query(Testcase)}
        count = get_build_phase_count(rs)
        runs = []
        for r in rs:
            if r.id > latest_id:
                runs.append({
                    'html': render_template('build_row.html', r=r, t=ts[r.testcase_id]),
                    'id': r.id,
                    'finished': r.status in ['passed', 'failed', 'timeout'],
                })
        if rs: latest_id = rs[-1].id
        return jsonify({
            'stamp': stamp,
            'latest_id': latest_id,
            'bar': render_template('build_bar.html', version=v, phase_count=count),
            'runs': runs ,
            'watch': watch,
            'auto_refresh': v.status not in ['passed', 'failed']
        })
    except:
        return abort(400)


@app.route(settings.WEBROOT + '/show/buildlog_<int:id>.html')
def download_buildlog(id):
    l = db_session.query(BuildLog).filter(BuildLog.id == id).first()
    if not l:
        return abort(404)
    path = os.path.join(settings.CORE_BUILD_LOG_PATH, '{:d}.txt'.format(l.id))
    if not os.path.exists(path):
        return abort(404)
    with open(path) as f:
        text = f.read()
    html = ansi2html(text, palette='console')
    return render_template('buildlog.html', log=html, buildlog=l)


@app.route(settings.WEBROOT + '/show/runlog_<int:id>.html')
def download_runlog(id):
    r = db_session.query(TestRun).filter(TestRun.id == id).first()
    if not r:
        return abort(404)
    path = os.path.join(settings.CORE_TESTRUN_STDERR_PATH, '{:d}.txt'.format(r.id))
    if not os.path.exists(path):
        return abort(404)
    with open(path) as f:
        text = f.read()
    html = ansi2html(text, palette='console')
    return render_template('runlog.html', log=html, testrun=r)


@app.route(settings.WEBROOT + '/download/testcase_<int:id>.txt')
def download_testcase(id):
    t = db_session.query(Testcase).filter(Testcase.id == id).first()
    if not t:
        return abort(404)
    if not t.is_public:
        return abort(401)
    text = utils.testcase_to_text(json.loads(t.content))
    return Response(text, content_type='text/plain; charset=utf-8')


@app.route(settings.WEBROOT + '/judges')
def judges():
    judges = sorted(judge_status.itervalues(), key=lambda x: x.time, reverse=True)
    return render_template('judges.html', judges=judges, now=datetime.utcnow())


def token_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.form.get('token', None)
        if token != settings.JUDGE_TOKEN:
            return abort(401)
        return f(*args, **kwargs)
    return decorated_function


@app.route(settings.WEBROOT + '/backend/dispatch/build', methods=['POST'])
@token_required
def backend_dispatch_build():
    judge = request.form['judge']
    version = db_session.query(Version)\
                        .filter(Version.phase == 'build', Version.status == 'pending')\
                        .order_by(Version.id.asc())\
                        .first()
    if not version:
        message = 'ask for build tasks, but not found'
        judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
        return jsonify({'found': False})
    compiler = db_session.query(Compiler).filter(Compiler.id == version.compiler_id).one()
    ret = {
        'found': True, 
        'compiler': copy_sqlalchemy_object_as_dict(compiler),
        'version': copy_sqlalchemy_object_as_dict(version)
    }
    version.status = 'building'
    db_session.commit()

    message = 'ask for build tasks. assigned build task for <a href="{url_version}">build {version_id}</a>'.format(
        url_version=url_for('build', id=version.id),
        version_id=version.id)
    judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
    return jsonify(ret)


@app.route(settings.WEBROOT + '/backend/submit/build_log', methods=['POST'])
@token_required
def backend_submit_build_log():
    id = int(request.form['id'])
    judge = request.form['judge']
    message = request.form['message']
    committed_at = utils.parse_to_utc(request.form['committed_at'])
    status = request.form['status']
    build_time = float(request.form['build_time'])
    log = request.form['log']

    version = db_session.query(Version).filter(Version.id == id).one()
    build_log = BuildLog(version_id=version.id,
                         build_time=build_time,
                         builder=judge,
                         created_at=datetime.utcnow())
    db_session.add(build_log)
    db_session.commit()
    with open(os.path.join(settings.CORE_BUILD_LOG_PATH, '{:d}.txt'.format(build_log.id)), 'w') as f:
        f.write(log)

    version.message = message
    version.committed_at = committed_at
    if status == 'ok':
        version.phase = settings.TEST_PHASES[0]
        version.status = 'pending'
    else:
        version.status = 'failed'
    db_session.commit()

    message = 'submit <a href="{url_log}">build log {log_id}</a> for <a href="{url_version}">build {version_id}</a>'.format(
        url_log=url_for('download_runlog', id=build_log.id),
        log_id=build_log.id,
        url_version=url_for('build', id=version.id),
        version_id=version.id)
    judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
    return jsonify({'ack': True})


@app.route(settings.WEBROOT + '/backend/dispatch/testrun', methods=['POST'])
@token_required
def backend_dispatch_testrun():
    judge = request.form['judge']
    t = db_session.query(TestRun)\
                  .filter(TestRun.status == 'pending')\
                  .order_by(TestRun.id.asc())\
                  .first()
    if not t:
        message = 'ask for run tasks, but not found'
        judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
        return jsonify({'found': False})
    v = db_session.query(Version).filter(Version.id == t.version_id).one()
    c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
    ret = {
        'found': True,
        'testrun': copy_sqlalchemy_object_as_dict(t),
        'version': copy_sqlalchemy_object_as_dict(v),
        'compiler': copy_sqlalchemy_object_as_dict(c)
    }
    t.status = 'running'
    t.dispatch_at = datetime.utcnow()
    db_session.commit()

    message = 'ask for run tasks. assigned run task for run {run_id}'.format(
        run_id=t.id)
    judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
    return jsonify(ret)


@app.route(settings.WEBROOT + '/backend/submit/testrun', methods=['POST'])
@token_required
def backend_submit_testrun():
    id = int(request.form['id'])
    judge = request.form['judge']
    status = request.form['status']
    running_time = float(request.form['running_time'])
    compile_time = float(request.form['compile_time'])
    stderr = request.form['stderr']

    r = db_session.query(TestRun).filter(TestRun.id == id).one()
    t = db_session.query(Testcase).filter(Testcase.id == r.testcase_id).one()
    r.finished_at = datetime.utcnow()
    r.running_time = running_time
    r.compile_time = compile_time
    r.status = status
    t.cnt_run = Testcase.cnt_run + 1
    if status != 'passed':
        t.cnt_hack = Testcase.cnt_hack + 1
    db_session.commit()
    path = os.path.join(settings.CORE_TESTRUN_STDERR_PATH, '{:d}.txt'.format(id))
    with open(path, 'w') as f:
        f.write(stderr)

    message = 'submit run result for <a href="{url_run}">run {run_id}</a>'.format(
        url_run=url_for('download_runlog', id=r.id),
        run_id=r.id)
    judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
    return jsonify({'ack': True})


@app.route(settings.WEBROOT + '/backend/download/testcase/<int:id>.json', methods=['POST'])
@token_required
def backend_download_testcase(id):
    t = db_session.query(Testcase).filter(Testcase.id == id).one()
    return Response(t.content, mimetype='application/json')
