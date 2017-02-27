# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import uuid
import json
import functools
from datetime import datetime
import StringIO
from flask import request, redirect, session, url_for, flash, render_template, jsonify, abort, send_file, Response

from web import app
from models import *
from database import db_session
import settings, utils


def copy_sqlalchemy_object_as_dict(o):
    d = dict(o.__dict__)
    del d['_sa_instance_state']
    return d


@app.route(settings.WEBROOT + '/download/testcase/<int:id>.txt')
def download_testcase(id):
    t = db_session.query(Testcase).filter(Testcase.id == id).first()
    if not t:
        return abort(404)
    if not t.is_public:
        return abort(401)
    text = utils.testcase_to_text(json.loads(t['content']))
    return Response(text, content_type='text/plain; charset=utf-8')


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
    version = db_session.query(Version)\
                        .filter(Version.phase == 'build', Version.status == 'pending')\
                        .order_by(Version.id.asc())\
                        .first()
    if not version:
        return jsonify({'found': False})
    compiler = db_session.query(Compiler).filter(Compiler.id == version.compiler_id).one()
    ret = {
        'found': True, 
        'compiler': copy_sqlalchemy_object_as_dict(compiler),
        'version': copy_sqlalchemy_object_as_dict(version)
    }
    version.status = 'building'
    db_session.commit()
    return jsonify(ret)


@app.route(settings.WEBROOT + '/backend/submit/build_log', methods=['POST'])
@token_required
def backend_submit_build_log():
    id = int(request.form['id'])
    print id
    judge = request.form['judge']
    print judge
    message = request.form['message']
    print message
    committed_at = utils.parse_to_utc(request.form['committed_at'])
    print committed_at
    status = request.form['status']
    print status
    build_time = float(request.form['build_time'])
    print build_time
    log = request.form['log']
    print log

    version = db_session.query(Version).filter(Version.id == id).one()
    build_log = BuildLog(version_id=version.id,
                         build_time=build_time,
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
    return jsonify({'ack': True})


@app.route(settings.WEBROOT + '/backend/dispatch/testrun', methods=['POST'])
@token_required
def backend_dispatch_testrun():
    t = db_session.query(TestRun)\
                  .filter(TestRun.status == 'pending')\
                  .order_by(TestRun.id.asc())\
                  .first()
    if not t:
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
    return jsonify(ret)


@app.route(settings.WEBROOT + '/backend/submit/testrun', methods=['POST'])
@token_required
def backend_submit_testrun():
    id = int(request.form['id'])
    judge = request.form['judge']
    status = request.form['status']
    running_time = float(request.form['running_time'])
    stderr = request.form['stderr']

    r = db_session.query(TestRun).filter(TestRun.id == id).one()
    r.finished_at = datetime.utcnow()
    r.running_time = running_time
    r.status = status
    db_session.commit()
    path = os.path.join(settings.CORE_TESTRUN_STDERR_PATH, '{:d}.txt'.format(id))
    with open(path, 'w') as f:
        f.write(stderr)
    return jsonify({'ack': True})


@app.route(settings.WEBROOT + '/backend/download/testcase/<int:id>.json', methods=['POST'])
@token_required
def backend_download_testcase(id):
    t = db_session.query(Testcase).filter(Testcase.id == id).one()
    return Response(t.content, mimetype='application/json')
