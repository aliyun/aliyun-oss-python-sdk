# -*- coding: utf-8 -*-

import unittest

import oss2
from oss2.exceptions import make_exception

import os
import sys
import tempfile
import requests
import datetime
import locale
import io
from functools import partial

from .common import *

import logging

try:
    xrange
except NameError:
    xrange = range


is_py2 = (sys.version_info[0] == 2)
is_py3 = (sys.version_info[0] == 3)


class TestUtils(OssTestCase):
    def test_is_ip(self):
        self.assertTrue(oss2.utils.is_ip_or_localhost('1.2.3.4'))
        self.assertTrue(oss2.utils.is_ip_or_localhost('[2401:b180::dc]'))
        self.assertTrue(oss2.utils.is_ip_or_localhost('localhost'))
        self.assertTrue(oss2.utils.is_ip_or_localhost('1.2.3.4:80'))
        self.assertTrue(oss2.utils.is_ip_or_localhost('[2401:b180::dc]:80'))
        self.assertTrue(oss2.utils.is_ip_or_localhost('localhost:80'))

        self.assertTrue(not oss2.utils.is_ip_or_localhost('-1.2.3.4'))
        self.assertTrue(not oss2.utils.is_ip_or_localhost('1.256.1.2'))
        self.assertTrue(not oss2.utils.is_ip_or_localhost('一.二.三.四'))
        self.assertTrue(not oss2.utils.is_ip_or_localhost('[2401:b180::dc'))

    def test_is_valid_bucket_name(self):
        self.assertTrue(oss2.is_valid_bucket_name('abc'))
        self.assertTrue(oss2.is_valid_bucket_name('hello-world'))

        self.assertTrue(not oss2.is_valid_bucket_name('HELLO'))
        self.assertTrue(not oss2.is_valid_bucket_name('hello_world'))
        self.assertTrue(not oss2.is_valid_bucket_name('hello-'))
        self.assertTrue(not oss2.is_valid_bucket_name('-hello'))

    def test_compat(self):
        # from unicode
        u = u'中文'

        self.assertEqual(u, oss2.to_unicode(u))
        self.assertEqual(u.encode('utf-8'), oss2.to_bytes(u))

        if is_py2:
            self.assertEqual(u.encode('utf-8'), oss2.to_string(u))

        if is_py3:
            self.assertEqual(u, oss2.to_string(u))

        # from bytes
        b = u.encode('utf-8')

        self.assertEqual(b.decode('utf-8'), oss2.to_unicode(b))
        self.assertEqual(b, oss2.to_bytes(b))

        if is_py2:
            self.assertEqual(b, oss2.to_string(b))

        if is_py3:
            self.assertEqual(b.decode('utf-8'), oss2.to_string(b))

    def test_makedir_p(self):
        tempdir = tempfile.gettempdir()

        dirpath = os.path.join(tempdir, random_string(10))

        oss2.utils.makedir_p(dirpath)
        os.path.isdir(dirpath)

        # recreate same dir should not issue an error
        oss2.utils.makedir_p(dirpath)

    def __fake_response(self, status, error_body):
        key = self.random_key()

        self.bucket.put_object(key, oss2.to_bytes(error_body))
        resp = self.bucket.get_object(key).resp
        resp.status = status

        return resp

    def test_make_exception(self):
        body = 'bad body'
        e = make_exception(self.__fake_response(400, body))
        self.assertTrue(isinstance(e, oss2.exceptions.ServerError))
        self.assertEqual(e.status, 400)
        self.assertEqual(e.body, oss2.to_bytes(body))

        body = '<Error><Code>NoSuchKey</Code><Message>中文和控制字符&#12;</Message></Error>'
        e = make_exception(self.__fake_response(404, body))
        self.assertTrue(isinstance(e, oss2.exceptions.NoSuchKey))
        self.assertEqual(e.status, 404)
        self.assertEqual(e.code, 'NoSuchKey')

    def test_len(self):
        adapter = oss2.utils.SizedFileAdapter('ss', 2500000000)
        self.assertEqual(requests.utils.super_len(adapter), 2500000000)

        adapter = oss2.utils._BytesAndFileAdapter('ss', size=2500000000)
        self.assertEqual(requests.utils.super_len(adapter), 2500000000)

    def test_adapter_composition(self):
        def progress_callback(consumed_bytes, total_bytes):
            pass

        crc_adapter = oss2.utils.make_crc_adapter('sss')
        progress_adapter = oss2.utils.make_progress_adapter(crc_adapter, progress_callback)

        self.assertEqual(progress_adapter.len, 3)

    def test_crc_and_cipher_adapter(self):

        crc_adapter = oss2.utils.make_crc_adapter('sss')
        cipher_adapter = oss2.utils.make_cipher_adapter(crc_adapter,
                    partial(oss2.utils.AESCipher.encrypt ,oss2.utils.AESCipher(b'1' * 32, 1)))

        content = cipher_adapter.read()

        self.assertEqual(cipher_adapter.crc, 10301458956098309249)

        with io.BytesIO(oss2.to_bytes('sss')) as f:
            crc_adapter = oss2.utils.make_crc_adapter(f)
            cipher_adapter = oss2.utils.make_cipher_adapter(crc_adapter,
                     partial(oss2.utils.AESCipher.encrypt, oss2.utils.AESCipher(b'1' * 32, 1)))

            content = cipher_adapter.read()

            self.assertEqual(cipher_adapter.crc, 10301458956098309249)



    def test_default_logger_basic(self):
        # verify default logger
        # self.assertEqual(oss2.defaults.get_logger(), logging.getLogger())

        # verify custom logger
        # custom_logger = logging.getLogger('oss2')
        # oss2.defaults.logger = custom_logger

        # self.assertEqual(oss2.defaults.get_logger(), custom_logger)
        custom_logger = logging.getLogger('oss2')
        self.assertEqual(oss2.logger, custom_logger)

    def test_default_logger_put(self):
        custom_logger = logging.getLogger('oss2')
        # oss2.defaults.logger = custom_logger

        custom_logger.addHandler(logging.StreamHandler(sys.stdout))
        custom_logger.setLevel(logging.DEBUG)

        key = self.random_key()

        self.bucket.put_object(key, 'abc')
        resp = self.bucket.get_object(key).resp

        self.assertEqual(b'abc', resp.read())

        custom_logger.setLevel(logging.CRITICAL)

    def test_http_to_unixtime_in_zh_CN_locale(self):
        time_string = 'Sat, 06 Jan 2018 00:00:00 GMT'
        time_val = 1515196800

        saved_locale = locale.setlocale(locale.LC_TIME)
        if os.name == 'nt':
            locale.setlocale(locale.LC_TIME, '')
        else:
            locale.setlocale(locale.LC_TIME, 'zh_CN.UTF-8')

        self.assertEqual(time_val, oss2.utils.http_to_unixtime(time_string))

        self.assertRaises(ValueError, oss2.utils.to_unixtime, time_string, '%a, %d %b %Y %H:%M:%S GMT')

        locale.setlocale(locale.LC_TIME, saved_locale)

    def test_http_to_unixtime_basic(self):
        case_list = [
            ('Sat, 06 Jan 2018 00:00:00 GMT', 1515196800),
            ('Fri, 09 Feb 2018 01:01:01 GMT', 1518138061),
            ('Sun, 11 Mar 2018 10:10:10 GMT', 1520763010),
            ('Mon, 23 Apr 2018 21:21:21 GMT', 1524518481),
            ('Thu, 31 May 2018 23:59:59 GMT', 1527811199),
            ('Wed, 20 Jun 2018 20:31:30 GMT', 1529526690),
            ('Tue, 10 Jul 2018 11:11:11 GMT', 1531221071),
            ('Tue, 21 Aug 1979 09:09:09 GMT', 304074549),
            ('Wed, 29 Sep 2100 10:21:32 GMT', 4125896492),
            ('Fri, 01 Oct 1999 08:00:00 GMT', 938764800),
            ('Wed, 11 Nov 2009 00:00:00 GMT', 1257897600),
            ('Wed, 12 Dec 2012 12:12:12 GMT', 1355314332)
        ]

        for time_string, time_val in case_list:
            t1 = oss2.utils.http_to_unixtime(time_string)
            t2 = oss2.utils.to_unixtime(time_string, '%a, %d %b %Y %H:%M:%S GMT')

            self.assertEqual(time_val, t1)
            self.assertEqual(time_val, t2)
            self.assertEqual(time_string, oss2.utils.http_date(time_val))

    def test_http_to_unixtime_one_day(self):
        now = int(time.time())
        for t in xrange(now, now + 86400):
            time_string = oss2.utils.http_date(t)
            self.assertEqual(t, oss2.utils.http_to_unixtime(time_string))

    def test_http_to_unixtime_one_year(self):
        now = int(time.time())

        for i in xrange(366):
            t = now + i * 86400
            time_string = oss2.utils.http_date(t)
            self.assertEqual(t, oss2.utils.http_to_unixtime(time_string))

    def test_http_to_unixtime_bad_format(self):
        case_list = [
            '',
            'Sat',
            'Sat, 06 ',
            'Sat, 06 Jan',
            'Sat, 06 Jan 20',
            'Sat, 06 Jan 2018 ',
            'Sat, 06 Jan 2018 00',
            'Sat, 06 Jan 2018 00:',
            'Sat, 06 Jan 2018 00:00:',
            'Sat, 06 Jan 2018 00:00:00',
            'Sat, 06 Jan 2018 00:00:00 G',
            'Unk, 06 Jan 2018 00:00:00 GMT',
            'Friday, 12 Dec 2012 12:12:12 GMT',
            'We, 12 Dec 2012 12:12:12 GMT',
            'Wed 12 Dec 2012 12:12:12 GMT',
            'Wed, 32 Dec 2012 12:12:12 GMT',
            'Wed, 31 December 2012 12:12:12 GMT',
            'Wed, 31 De 2012 12:12:12 GMT',
            'Wed, 31 2012 12:12:12 GMT',
            'Wed, 12 Dec 12:12:12 GMT',
            'Wed, 31 Dec 2012 24:12:12 GMT',
            'Wed, 31 Dec 2012 23:60:12 GMT',
            'Wed, 31 Dec 2012 23:10:60 GMT',
            'Wed, 31 Dec 2012 2:10:60 GMT',
            'Wed, 31 Dec 2012 :10:60 GMT',
            'Wed, 31 Dec 2012 02:1:60 GMT',
            'Wed, 31 Dec 2012 02:01:0 GMT',
            'Wed, 31 Dec 2012 02:01:01 CST',
            'Wed, 31 Dec 2012 02:01:01 GMTA',
            'Wed, 31 Dec 2012 02:01:01 GMT ABC',
            'X  Wed, 31 Dec 2012 02:01:01 GMT',
            '  Wed, 31 Dec 2012 02:01:01 GMT'
        ]

        for bad_string in case_list:
            try:
                oss2.utils.http_to_unixtime(bad_string)
            except ValueError as e:
                self.assertEqual(str(e), bad_string + ' is not in valid HTTP date format')
            else:
                self.assertTrue(False, bad_string)

    def test_iso8601_to_unixtime_in_zh_CN_locale(self):
        time_string = '2018-02-09T01:01:01.000Z'
        time_val = 1518138061

        saved_locale = locale.setlocale(locale.LC_TIME)
        
        if os.name == 'nt':
            locale.setlocale(locale.LC_TIME, '')
        else:
            locale.setlocale(locale.LC_TIME, 'zh_CN.UTF-8')

        # iso8601 contains no locale related info, so it is OK to use to_unixtime()
        self.assertEqual(time_val, oss2.utils.iso8601_to_unixtime(time_string))
        self.assertEqual(time_val, oss2.utils.to_unixtime(time_string, '%Y-%m-%dT%H:%M:%S.000Z'))

        locale.setlocale(locale.LC_TIME, saved_locale)

    def test_iso8601_to_unixtime_basic(self):
        case_list = [
            ('2018-01-06T00:00:00.000Z', 1515196800),
            ('2018-02-09T01:01:01.000Z', 1518138061),
            ('2018-03-11T10:10:10.000Z', 1520763010),
            ('2018-04-23T21:21:21.000Z', 1524518481),
            ('2018-05-31T23:59:59.000Z', 1527811199),
            ('2018-06-20T20:31:30.000Z', 1529526690),
            ('2018-07-10T11:11:11.000Z', 1531221071),
            ('1979-08-21T09:09:09.000Z', 304074549),
            ('2100-09-29T10:21:32.000Z', 4125896492),
            ('1999-10-01T08:00:00.000Z', 938764800),
            ('2009-11-11T00:00:00.000Z', 1257897600),
            ('2012-12-12T12:12:12.000Z', 1355314332)
        ]

        for time_string, time_val in case_list:
            t1 = oss2.utils.iso8601_to_unixtime(time_string)
            t2 = oss2.utils.to_unixtime(time_string, '%Y-%m-%dT%H:%M:%S.000Z')

            self.assertEqual(time_val, t1)
            self.assertEqual(time_val, t2)
            self.assertEqual(time_string, oss2.utils.date_to_iso8601(datetime.datetime.utcfromtimestamp(time_val)))

    def test_iso8601_to_unixtime_one_day(self):
        now = int(time.time())
        for t in xrange(now, now + 86400):
            time_string = oss2.utils.date_to_iso8601(datetime.datetime.utcfromtimestamp(t))
            self.assertEqual(t, oss2.utils.iso8601_to_unixtime(time_string))

    def test_iso8601_to_unixtime_one_year(self):
        now = int(time.time())

        for i in xrange(366):
            t = now + i * 86400
            time_string = oss2.utils.date_to_iso8601(datetime.datetime.utcfromtimestamp(t))
            self.assertEqual(t, oss2.utils.iso8601_to_unixtime(time_string))

    def test_iso8601_to_unixtime_bad_format(self):
        case_list = [
            '',
            '2012',
            '2012-',
            '2012-12',
            '2012-12-',
            '2012-12-12',
            '2012-12-12T',
            '2012-12-12T12',
            '2012-12-12T12:',
            '2012-12-12T12:1',
            '2012-12-12T12:12:',
            '2012-12-12T12:12:12',
            '2012-12-12T12:12:12.',
            '2012-12-12T12:12:12.0',
            '2012-12-12T12:12:12.00',
            '2012-12-12T12:12:12.000',
            '2012-12-12T12:12:12.000X',
            '-12-12T12:12:12.000Z',
            '2012-13-12T12:12:12.000Z',
            '2012-12-32T12:12:12.000Z',
            '2012-12-12X12:12:12.000Z',
            '2012-12-12T:12:12.000Z',
            '2012-12-12T0:12:12.000Z',
            '2012-12-12T60:12:12.000Z',
            '2012-12-12T12::12.000Z',
            '2012-12-12T12:1:12.000Z',
            '2012-12-12T12:60:12.000Z',
            '2012-12-12T12:12:1.000Z',
            '2012-12-12T12:12:60.000Z',
            '2012-12-12T12:12:12.100Z',
            '2012-12-12T12:12:12.010Z',
            '2012-12-12T12:12:12.001Z',
            '2012-12-12T12:12:12.000ZZ',
            '2012-12-12T12:12:12.000Z X',
            '2012-12-12T12:12:00.000Z ',
            ' 2012-12-12T12:12:00.000Z',
            'X 2012-12-12T12:12:00.000Z',
        ]

        for bad_string in case_list:
            try:
                oss2.utils.iso8601_to_unixtime(bad_string)
            except ValueError as e:
                self.assertEqual(str(e), bad_string + ' is not in valid ISO8601 format')
            else:
                self.assertTrue(False, bad_string)


if __name__ == '__main__':
    unittest.main()