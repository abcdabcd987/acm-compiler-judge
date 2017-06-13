#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
import os
import csv
import sys
import time
import json
import shutil
import codecs
import hashlib
import StringIO
from datetime import datetime
from collections import namedtuple
from jinja2 import Environment, PackageLoader, select_autoescape, Template

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
        version = db_session.query(Version).filter(Version.id == compiler.latest_version_id).first()
        if not version:
            continue
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


def final_rejudge():
    if len(sys.argv) != 4:
        print('usage: ./maintenance.py final_rejudge <input_csv> <output_csv>')
        sys.exit(1)

    compilers = {c.id: c for c in db_session.query(Compiler)}
    submit_versions = set()
    with open(sys.argv[2]) as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        for row in reader:
            cid = int(row['cid'])
            assert cid in compilers
            assert compilers[cid].student == row['name'].decode('utf-8')
            for col in fieldnames:
                value = row[col]
                if col.decode('utf-8') in ('cid', 'name') or not value:
                    continue
                submit_versions.add(int(value))
    with open(sys.argv[2]) as fin, open(sys.argv[3], 'w') as fout:
        rejudge_versions = {}
        for version_id in submit_versions:
            old = db_session.query(Version).filter(Version.id == version_id).one()
            new = Version(compiler_id=old.compiler_id,
                          sha=old.sha,
                          phase='build',
                          status='pending')
            db_session.add(new)
            db_session.commit()
            rejudge_versions[old.id] = new.id

        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames)
        writer.writeheader()
        for row in reader:
            for col in fieldnames:
                value = row[col]
                if col.decode('utf-8') in ('cid', 'name') or not value:
                    continue
                row[col] = rejudge_versions[int(value)]
            writer.writerow(row)
    print('done!', len(rejudge_versions), 'submits to run')


def generate_final_result():
    if len(sys.argv) != 4:
        print('usage: ./maintenance.py generate_final_result <rejudge_csv> <output_dir>')
        sys.exit(1)
    #  rank     1   2   3   4   5   6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21
    SCORE = [0, 15, 14, 13, 11, 11, 9, 9, 7, 7, 7, 5, 5, 5, 5, 5, 3, 3, 3, 3, 3, 1]
    DISCOUNT = {'0531': 0, '0601': 1, '0602': 1+2, '0603': 1+2+3, '0611': 1+2+3+4}


    def set_rank(l, key):
        last_value = None
        last_rank = None
        for i, d in enumerate(l, start=1):
            value = float('{:.3f}'.format(d[key]))
            if value != last_value:
                last_value = value
                last_rank = i
            d['rank'] = last_rank
    
    def gen_testcase_rank(versions, version_ids):
        testcases = {}
        for version_id in version_ids:
            for t in versions[version_id]['testcase'].itervalues():
                if t.testcase_id not in testcases:
                    testcases[t.testcase_id] = []
                if t.status == 'passed':
                    testcases[t.testcase_id].append(dict(t.__dict__))
        for t in testcases:
            l = sorted(testcases[t], key=lambda testcase: testcase['running_time'])
            set_rank(l, 'running_time')
            for d in l:
                rank = d['rank']
                d['points'] = 31 - rank

            running_times = map(lambda testcase: testcase['running_time'], l)
            median = running_times[len(running_times) // 2]
            if len(running_times) % 2 == 0:
                median += running_times[len(running_times) // 2 - 1]
                median /= 2
            
            testcases[t] = {
                'testcase_id': t,
                'list': l,
                'vmap': {x['version_id']: x for x in l},
                'min': running_times[0],
                'max': running_times[-1],
                'avg': sum(running_times) / len(running_times),
                'median': median,
            }
        for t in testcases.keys():
            if testcases[t]['max'] < 0.1:
                del testcases[t]
        return testcases
    
    def gen_person_rank(rejudge_table, versions, testcase_rank, discount):
        people = {cid: {'points': 0, 'cid': cid} for cid in rejudge_table}
        for t in testcase_rank.itervalues():
            for d in t['list']:
                version_id = d['version_id']
                cid = versions[version_id]['version'].compiler_id
                people[cid]['points'] += d['points']
                people[cid]['version_id'] = version_id
        for cid in people.keys():
            if 'version_id' not in people[cid]:
                del people[cid]
        people = sorted(people.itervalues(), key=lambda x: x['points'], reverse=True)
        set_rank(people, 'points')
        for person in people:
            score = SCORE[person['rank']] if person['rank'] < len(SCORE) else SCORE[-1]
            person['score'] = 85 + score
            person['discounted_score'] = person['score'] * (1.0 - discount / 100.0)
        return people
    
    def gen_final_rank(person_rank):
        final_dict = {}
        for day in person_rank:
            for person in person_rank[day]:
                cid = person['cid']
                if cid not in final_dict:
                    final_dict[cid] = {}
                final_dict[cid][day] = person['discounted_score']
        for cid, d in final_dict.iteritems():
            max_score, max_day = None, None
            for day, score in d.iteritems():
                if max_score is None or score > max_score:
                    max_score = score
                    max_day = day
            d['max_score'], d['max_day'] = max_score, max_day
            d['cid'] = cid
        final = sorted(final_dict.itervalues(), key=lambda x: x['max_score'], reverse=True)
        set_rank(final, 'max_score')
        return final
        

    # fetch all kinds of information
    compilers = {c.id: c for c in db_session.query(Compiler)}
    rejudge_versions = set()
    rejudge_table = {}
    with open(sys.argv[2]) as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        for row in reader:
            d = {}
            cid = int(row['cid'])
            assert cid in compilers
            assert compilers[cid].student == row['name'].decode('utf-8')
            for col in fieldnames:
                value = row[col]
                if col.decode('utf-8') in ('cid', 'name') or not value:
                    continue
                rejudge_versions.add(int(value))
                d[col] = int(value)
            rejudge_table[cid] = d
    versions = {v.id: {'version': v, 'testcase': {}}
                for v in db_session.query(Version).filter(Version.id.in_(rejudge_versions))}
    query = db_session.query(TestRun) \
                      .filter(TestRun.version_id.in_(rejudge_versions)) \
                      .filter(TestRun.phase.in_(['optim pretest', 'optim extended']))

    for t in query:
        versions[t.version_id]['testcase'][t.testcase_id] = t
    days = list(fieldnames)
    days.remove('cid')
    days.remove('name')

    # setup output environment
    output_dir = sys.argv[3]
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    env = Environment(
        loader=PackageLoader('core', 'templates'),
        autoescape=select_autoescape(['html', 'xml']),
    )
    env.filters['nl2monobr'] = utils.nl2monobr
    env.globals.update(website_name=settings.WEBSITE_NAME)
    env.globals.update(ROOT=settings.WEBROOT)
    env.globals.update(FINAL_ROOT=settings.FINAL_ROOT)

    # generate testcase rank
    testcase_rank = gen_testcase_rank(versions, rejudge_versions)
    template = env.get_template('final_testcase.html')
    os.makedirs(os.path.join(output_dir, 'all'))
    for t, d in testcase_rank.iteritems():
        filename = os.path.join(output_dir, 'all', 'testcase-{}.html'.format(t))
        with codecs.open(filename, 'w', 'utf-8') as f:
            f.write(template.render(compilers=compilers,
                                    versions=versions,
                                    day='All',
                                    show_score=False,
                                    **d))
    
    # generate daily rank
    testcase_rank = {}
    person_rank = {}
    for day in days:
        # collect version_ids
        version_ids = set()
        for cid in rejudge_table:
            version_id = rejudge_table[cid].get(day, None)
            if version_id and versions[version_id]['version'].phase == 'end':
                version_ids.add(version_id)
        
        # generate daily testcase rank
        testcase_rank[day] = gen_testcase_rank(versions, version_ids)
        template = env.get_template('final_testcase.html')
        os.makedirs(os.path.join(output_dir, day))
        for t, d in testcase_rank[day].iteritems():
            filename = os.path.join(output_dir, day, 'testcase-{}.html'.format(t))
            with codecs.open(filename, 'w', 'utf-8') as f:
                f.write(template.render(compilers=compilers, 
                                        versions=versions,
                                        day=day,
                                        show_score=True,
                                        **d))
        
        # generate daily person rank
        person_rank[day] = gen_person_rank(rejudge_table, versions, testcase_rank[day], DISCOUNT[day])
        testcase_list = sorted(testcase_rank[day].iterkeys())
        template = env.get_template('final_person.html')
        filename = os.path.join(output_dir, day, 'result.html')
        with codecs.open(filename, 'w', 'utf-8') as f:
            f.write(template.render(compilers=compilers,
                                    versions=versions,
                                    testcase_rank=testcase_rank[day],
                                    testcase_list=testcase_list,
                                    discount=DISCOUNT[day],
                                    day=day,
                                    people=person_rank[day]))
    
    # generate final rank
    final_rank = gen_final_rank(person_rank)
    template = env.get_template('final_rank.html')
    filename = os.path.join(output_dir, 'result.html')
    with codecs.open(filename, 'w', 'utf-8') as f:
        f.write(template.render(compilers=compilers,
                                versions=versions,
                                final_rank=final_rank,
                                DISCOUNT=DISCOUNT,
                                days=days))


if __name__ == '__main__':
    actions = [
        add_compiler,
        add_testcase,
        set_testcase,
        rejudge_version,
        initdb,
        makedirs,
        clear_judge_testcase_cache,
        final_rejudge,
        generate_final_result,
    ]
    action_map = {func.__name__: func for func in actions}
    if len(sys.argv) < 2 or sys.argv[1] not in action_map:
        print('usage: ./maintenance.py <action>')
        print('<action> can be:')
        for k in actions:
            print('    %s' % k.__name__)
        sys.exit(1)
    action_map[sys.argv[1]]()
