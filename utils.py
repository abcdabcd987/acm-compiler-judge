# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
import time
import pytz
import arrow
import StringIO
import dateutil.parser
from datetime import datetime

import settings


def format_from_utc(dt):
    if not dt: return ''
    dt = settings.TIMEZONE.fromutc(dt.replace(tzinfo=settings.TIMEZONE))
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def parse_datetime(value):
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')


def local_to_utc(local):
    return settings.TIMEZONE.localize(local, is_dst=False).astimezone(pytz.utc)


def parse_to_utc(s):
    d = dateutil.parser.parse(s)
    epoch = time.mktime(d.timetuple()) - d.utcoffset().total_seconds()
    return datetime.fromtimestamp(epoch)


def nl2p(text):
    return ''.join("<p>%s</p>" % line for line in text.splitlines() if line)


def time_from_now(utc_datetime):
    return arrow.Arrow.fromdatetime(utc_datetime).humanize() if utc_datetime else ''


def nl2monobr(text):
    if not text: return ''
    return '<div style="font-family: monospace">' + '<br>'.join(text.splitlines()) + '</div>'


def multiline_indent(text, indent='    '):
    if not text: return ''
    return '\n'.join([indent + line for line in text.splitlines()])


def testcase_tooltip(testcase):
    pr = 100.0 - testcase.cnt_hack * 100.0 / testcase.cnt_run if testcase.cnt_run else 0.0
    return '''=== Testcase {0.id} ===
enabled: {0.enabled}
phase: {0.phase}
{3}hack/run: {0.cnt_hack}/{0.cnt_run}
pass rate: {1:.1f}%
comment:
{2}'''.format(testcase, pr,
    multiline_indent(testcase.comment, indent='&nbsp;&nbsp;&nbsp;&nbsp;'),
    'timeout: {:.3f}s\n'.format(testcase.timeout) if testcase.timeout else '')


def label_class(status):
    return {
        'passed': 'success',
        'failed': 'danger',
        'timeout': 'warning',
        'building': 'building',
        'running': 'info',
    }.get(status, 'default')


def phase_to_index(phase):
    return (['build'] + settings.TEST_PHASES + ['end']).index(phase)


def version_count_tooltip(cnt):
    sio = StringIO.StringIO()
    sio.write('build: ')
    sio.write(cnt['build'])
    sio.write('\n')
    for phase in settings.TEST_PHASES:
        sio.write(phase)
        sio.write(': ')
        c = cnt[phase]
        sio.write('{}/{}'.format(c[0], c[1]) if c else 'n/a')
        sio.write('\n')
    return sio.getvalue()


def normalize_nl(text):
    return '\n\n'.join(line for line in text.splitlines() if line)


def testcase_to_text(t):
    sio = StringIO.StringIO()
    print >> sio, t['program']
    print >> sio, '\n/*!! metadata:'
    for key, value in t.iteritems():
        if key != 'program':
            print >> sio, '=== {} ==='.format(key)
            print >> sio, value
    print >> sio, '\n!!*/\n'
    return sio.getvalue()


def parse_testcase(content):
    meta_start = '/*!! metadata:'
    meta_end = '!!*/'
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == meta_start:
            break
    t = {'program': '\n'.join(lines[:i])}
    key_pattern = re.compile('===(.*?)===')
    key, st = None, i+1
    for i, line in enumerate(lines[i+1:], start=i+1):
        stripped = lines[i].strip()
        match = key_pattern.match(stripped)
        if (match or stripped == meta_end) and key:
            value = '\n'.join(lines[st:i])
            t[key] = value.strip()
        if match:
            key = match.group(1).strip()
            st = i+1
        elif stripped == meta_end:
            break
    assert t['assert'] in ['success_compile', 'failure_compile', 'exitcode', 'runtime_error', 'output']
    if t['assert'] not in ['success_compile', 'failure_compile']:
        if t['assert'] == 'exitcode':
            t['timeout'] = float(t['timeout'])
            t['exitcode'] = int(t['exitcode'])
            assert 0 <= t['exitcode'] <= 255
        elif t['assert'] == 'output':
            t['timeout'] = float(t['timeout'])
            assert 'output' in t
        assert 'input' in t
    assert t['phase'] in settings.TEST_PHASES
    assert 'comment' in t
    assert t['is_public'] in ['True', 'False']
    t['is_public'] = t['is_public'] == 'True'

    return t
