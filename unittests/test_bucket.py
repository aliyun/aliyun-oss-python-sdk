# -*- coding: utf-8 -*-

import unittest
import datetime

from mock import patch
from functools import partial
from xml.dom import minidom

from oss2 import to_string, to_bytes
from common import *


def all_tags(parent, tag):
    return [to_string(node.text) or '' for node in parent.findall(tag)]


def r4get_meta(body, in_status=200, in_headers=None):
    headers = oss2.CaseInsensitiveDict({
        'Server': 'AliyunOSS',
        'Date': 'Fri, 11 Dec 2015 11:40:31 GMT',
        'Content-Type': 'application/xml',
        'Content-Length': str(len(body)),
        'Connection': 'keep-alive',
        'x-oss-request-id': '566AB62EB06147681C283D73'
    })

    merge_headers(headers, in_headers)

    return MockResponse(in_status, headers, body)


def do4body(req, timeout,
            req_info=None,
            data_type=DT_BYTES,
            status=200,
            body=None):
    data = read_data(req.data, data_type)

    resp = r4get_meta(body, in_status=status)

    if req_info:
        req_info.req = req
        req_info.size = get_length(req.data)
        req_info.data = data
        req_info.resp = resp

    return resp


class TestBucket(unittest.TestCase):
    def assertSortedListEqual(self, a, b, key=None):
        self.assertEqual(sorted(a, key=key), sorted(b, key=key))

    def assertXmlEqual(self, a, b):
        normalized_a = minidom.parseString(to_bytes(a)).toxml(encoding='utf-8')
        normalized_b = minidom.parseString(to_bytes(b)).toxml(encoding='utf-8')

        self.assertEqual(normalized_a, normalized_b)

    @patch('oss2.Session.do_request')
    def test_create(self, do_request):
        resp = r4put(in_headers={'Location': '/ming-oss-share'})
        do_request.return_value = resp

        result = bucket().create_bucket(oss2.BUCKET_ACL_PRIVATE)
        self.assertEqual(resp.headers['x-oss-request-id'], result.request_id)

    @patch('oss2.Session.do_request')
    def test_put_acl(self, do_request):
        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4put, req_info=req_info, data_type=DT_BYTES)

        bucket().put_bucket_acl(oss2.BUCKET_ACL_PRIVATE)
        self.assertEqual(req_info.req.headers['x-oss-acl'], 'private')

        bucket().put_bucket_acl(oss2.BUCKET_ACL_PUBLIC_READ)
        self.assertEqual(req_info.req.headers['x-oss-acl'], 'public-read')

        bucket().put_bucket_acl(oss2.BUCKET_ACL_PUBLIC_READ_WRITE)
        self.assertEqual(req_info.req.headers['x-oss-acl'], 'public-read-write')

    @patch('oss2.Session.do_request')
    def test_get_acl(self, do_request):
        template = '''<?xml version="1.0" encoding="UTF-8"?>
        <AccessControlPolicy>
            <Owner>
                <ID>1047205513514293</ID>
                <DisplayName>1047205513514293</DisplayName>
            </Owner>
            <AccessControlList>
                <Grant>{0}</Grant>
            </AccessControlList>
        </AccessControlPolicy>
        '''

        for permission in ['private', 'public-read', 'public-read-write']:
            do_request.return_value = r4get_meta(template.format(permission))
            self.assertEqual(bucket().get_bucket_acl().acl, permission)

    @patch('oss2.Session.do_request')
    def test_put_logging(self, do_request):
        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4put, req_info=req_info, data_type=DT_BYTES)

        template = '<BucketLoggingStatus><LoggingEnabled><TargetBucket>fake-bucket</TargetBucket>' + \
                   '<TargetPrefix>{0}</TargetPrefix></LoggingEnabled></BucketLoggingStatus>'

        target_bucket_name = 'fake-bucket'
        for prefix in [u'日志+/', 'logging/', '日志+/']:
            bucket().put_bucket_logging(oss2.models.BucketLogging(target_bucket_name, prefix))
            self.assertXmlEqual(req_info.data, template.format(to_string(prefix)))

    @patch('oss2.Session.do_request')
    def test_get_logging(self, do_request):
        target_bucket_name = 'fake-bucket'

        template = '''<?xml version="1.0" encoding="UTF-8"?>
        <BucketLoggingStatus>
            <LoggingEnabled>
                <TargetBucket>fake-bucket</TargetBucket>
                <TargetPrefix>{0}</TargetPrefix>
            </LoggingEnabled>
        </BucketLoggingStatus>'''

        for prefix in [u'日志%+/*', 'logging/', '日志%+/*']:
            do_request.return_value = r4get_meta(template.format(to_string(prefix)))
            result = bucket().get_bucket_logging()

            self.assertEqual(result.target_bucket, target_bucket_name)
            self.assertEqual(result.target_prefix, to_string(prefix))

    @patch('oss2.Session.do_request')
    def test_put_website(self, do_request):
        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4put, req_info=req_info, data_type=DT_BYTES)

        template = '<WebsiteConfiguration><IndexDocument><Suffix>{0}</Suffix></IndexDocument>' + \
            '<ErrorDocument><Key>{1}</Key></ErrorDocument></WebsiteConfiguration>'

        for index, error in [('index+中文.html', 'error.中文') ,(u'中-+()文.index', u'@#$%中文.error')]:
            bucket().put_bucket_website(oss2.models.BucketWebsite(index, error))
            self.assertXmlEqual(req_info.data, template.format(to_string(index), to_string(error)))

    @patch('oss2.Session.do_request')
    def test_get_website(self, do_request):
        template = '<WebsiteConfiguration><IndexDocument><Suffix>{0}</Suffix></IndexDocument>' + \
            '<ErrorDocument><Key>{1}</Key></ErrorDocument></WebsiteConfiguration>'

        for index, error in [('index+中文.html', 'error.中文') ,(u'中-+()文.index', u'@#$%中文.error')]:
            do_request.return_value = r4get_meta(template.format(to_string(index), to_string(error)))

            result = bucket().get_bucket_website()
            self.assertEqual(result.index_file, to_string(index))
            self.assertEqual(result.error_file, to_string(error))

    @patch('oss2.Session.do_request')
    def test_put_lifecycle_date(self, do_request):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        template = '<LifecycleConfiguration><Rule><ID>{0}</ID><Prefix>{1}</Prefix>' + \
                   '<Status>{2}</Status><Expiration><Date>{3}</Date></Expiration></Rule></LifecycleConfiguration>'

        req_info = RequestInfo()
        do_request.auto_spec = True
        do_request.side_effect = partial(do4put, req_info=req_info, data_type=DT_BYTES)

        id = 'hello world'
        prefix = '中文前缀'
        status = 'Disabled'
        date = '2015-12-25T00:00:00.000Z'

        rule = LifecycleRule(id, prefix,
                             status=LifecycleRule.DISABLED,
                             expiration=LifecycleExpiration(date=datetime.date(2015, 12, 25)))
        bucket().put_bucket_lifecycle(BucketLifecycle([rule]))

        self.assertXmlEqual(req_info.data, template.format(id, prefix, status, date))

    @patch('oss2.Session.do_request')
    def test_put_lifecycle_days(self, do_request):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        template = '<LifecycleConfiguration><Rule><ID>{0}</ID><Prefix>{1}</Prefix>' + \
                   '<Status>{2}</Status><Expiration><Days>{3}</Days></Expiration></Rule></LifecycleConfiguration>'

        req_info = RequestInfo()
        do_request.auto_spec = True
        do_request.side_effect = partial(do4put, req_info=req_info, data_type=DT_BYTES)

        id = '中文ID'
        prefix = '中文前缀'
        status = 'Enabled'
        days = 3

        rule = LifecycleRule(id, prefix,
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=days))
        bucket().put_bucket_lifecycle(BucketLifecycle([rule]))

        self.assertXmlEqual(req_info.data, template.format(id, prefix, status, days))

    @patch('oss2.Session.do_request')
    def test_get_lifecycle_date(self, do_request):
        from oss2.models import LifecycleRule

        template = '<LifecycleConfiguration><Rule><ID>{0}</ID><Prefix>{1}</Prefix>' + \
                   '<Status>{2}</Status><Expiration><Date>{3}</Date></Expiration></Rule></LifecycleConfiguration>'

        id = 'whatever'
        prefix = 'lifecycle rule 1'
        status = LifecycleRule.DISABLED
        date = datetime.date(2015, 12, 25)

        do_request.return_value = r4get_meta(template.format(id, prefix, status, oss2.date_to_iso8601(date)))

        result = bucket().get_bucket_lifecycle()

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, date)
        self.assertEqual(rule.expiration.days, None)

    @patch('oss2.Session.do_request')
    def test_get_lifecycle_days(self, do_request):
        from oss2.models import LifecycleRule

        template = '<LifecycleConfiguration><Rule><ID>{0}</ID><Prefix>{1}</Prefix>' + \
                   '<Status>{2}</Status><Expiration><Days>{3}</Days></Expiration></Rule></LifecycleConfiguration>'

        id = '1-2-3'
        prefix = '中+-*%^$#@!文'
        status = LifecycleRule.ENABLED
        days = 356

        do_request.return_value = r4get_meta(template.format(id, prefix, status, days))

        result = bucket().get_bucket_lifecycle()

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, None)
        self.assertEqual(rule.expiration.days, days)

    @patch('oss2.Session.do_request')
    def test_put_cors(self, do_request):
        import xml.etree.ElementTree as ElementTree

        req_info = RequestInfo()
        do_request.auto_spec = True
        do_request.side_effect = partial(do4put, req_info=req_info, data_type=DT_BYTES)

        rule1 = oss2.models.CorsRule(allowed_origins=['*'],
                                     allowed_methods=['HEAD', 'GET'],
                                     allowed_headers=['*'],
                                     expose_headers=['x-oss-request-id'],
                                     max_age_seconds=1000)

        rule2 = oss2.models.CorsRule(allowed_origins=['http://*.aliyuncs.com'],
                                     allowed_methods=['HEAD'],
                                     allowed_headers=['Authorization'],
                                     max_age_seconds=1)
        rules = [rule1, rule2]

        cors = oss2.models.BucketCors(rules)
        bucket().put_bucket_cors(cors)

        root = ElementTree.fromstring(req_info.data)
        for i, rule_node in enumerate(root.findall('CORSRule')):
            self.assertSortedListEqual(rules[i].allowed_origins, all_tags(rule_node, 'AllowedOrigin'))
            self.assertSortedListEqual(rules[i].allowed_methods, all_tags(rule_node, 'AllowedMethod'))
            self.assertSortedListEqual(rules[i].allowed_headers, all_tags(rule_node, 'AllowedHeader'))
            self.assertSortedListEqual(rules[i].expose_headers, all_tags(rule_node, 'ExposeHeader'))

            self.assertEqual(rules[i].max_age_seconds, int(rule_node.find('MaxAgeSeconds').text))

    @patch('oss2.Session.do_request')
    def test_get_cors(self, do_request):
        body = b'''<CORSConfiguration>
            <CORSRule>
                <AllowedOrigin>*</AllowedOrigin>
                <AllowedMethod>PUT</AllowedMethod>
                <AllowedMethod>GET</AllowedMethod>
                <AllowedHeader>Authorization</AllowedHeader>
            </CORSRule>
            <CORSRule>
                <AllowedOrigin>http://www.a.com</AllowedOrigin>
                <AllowedOrigin>www.b.com</AllowedOrigin>
                <AllowedMethod>GET</AllowedMethod>
                <AllowedHeader>Authorization</AllowedHeader>
                <ExposeHeader>x-oss-test</ExposeHeader>
                <ExposeHeader>x-oss-test1</ExposeHeader>
                <MaxAgeSeconds>100</MaxAgeSeconds>
            </CORSRule>
        </CORSConfiguration>'''

        do_request.return_value = r4get_meta(body)

        rules = bucket().get_bucket_cors().rules
        self.assertEqual(rules[0].allowed_origins, ['*'])
        self.assertEqual(rules[0].allowed_methods, ['PUT', 'GET'])
        self.assertEqual(rules[0].allowed_headers, ['Authorization'])

        self.assertEqual(rules[1].allowed_origins, ['http://www.a.com', 'www.b.com'])
        self.assertEqual(rules[1].allowed_methods, ['GET'])
        self.assertEqual(rules[1].expose_headers, ['x-oss-test', 'x-oss-test1'])
        self.assertEqual(rules[1].max_age_seconds, 100)