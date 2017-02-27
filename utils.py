# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time
import pytz
import StringIO
import dateutil.parser
from datetime import datetime

import settings


def format_from_utc(dt):
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


def normalize_nl(text):
    return '\n\n'.join(line for line in text.splitlines() if line)


def testcase_to_text(t):
    sio = StringIO.StringIO()
    print >> sio, t['program']
    print >> sio, '\n/* metadata:'
    for key, value in t.iteritems():
        if key != 'program':
            print >> sio, '=== {} ==='.format(key)
            print >> sio, value
    print >> sio, '\n*/\n'
    return sio.getvalue()


# def parse_testcase(content):
#     t = {}
#     t['raw'] = content
#     starting = '/*#!>'
#     lines = content.splitlines()
#     for i, line in enumerate(lines):
#         if line.strip() == starting:
#             break
#     t['content'] = '\n'.join(lines[:i])

#     i += 1
#     while i < len(lines):
#         key, value = lines[i].split(': ', 1)
#         if value.startswith('<<<'):
#             j = i+1
#             while not lines[j].startswith('>>>'):
#                 j += 1
#             t[key] = '\n'.join(lines[i+1:j])
#             i = j+1
#         else:
#             t[key] = value.strip()
#             i += 1

#     t['timeout'] = float(t['timeout'])
#     return t

