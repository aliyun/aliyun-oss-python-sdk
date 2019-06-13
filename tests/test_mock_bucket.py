# -*- coding: utf-8 -*-

import unittest
import datetime

from mock import patch
from functools import partial

import oss2
import unittests

def all_tags(parent, tag):
    return [oss2.to_string(node.text) or '' for node in parent.findall(tag)]


class TestBucket(unittests.common.OssTestCase):
    @patch('oss2.Session.do_request')
    def test_create(self, do_request):
        request_text = '''PUT / HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 0
x-oss-acl: private
date: Sat, 12 Dec 2015 00:35:27 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:gyfUwtbRSPxjlqBymPKUp+ypQmw='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:27 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BCF6078C0E4487474E1
Location: /ming-oss-share'''

        req_info = unittests.common.mock_response(do_request, response_text)
        unittests.common.bucket().create_bucket(oss2.BUCKET_ACL_PRIVATE)

        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_put_acl(self, do_request):
        acls = [(oss2.BUCKET_ACL_PRIVATE, 'private'),
                (oss2.BUCKET_ACL_PUBLIC_READ, 'public-read'),
                (oss2.BUCKET_ACL_PUBLIC_READ_WRITE, 'public-read-write')]

        for acl_defined, acl_str in acls:
            request_text = '''PUT /?acl= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Content-Length: 0
x-oss-acl: {0}
Connection: keep-alive
date: Sat, 12 Dec 2015 00:36:26 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:CnQnJh9SA9f+ysU9YN8y/4lRD4E='''.format(acl_str)

            response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:36:26 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6C0AE36A00D566765067
Location: /ming-oss-share'''

            req_info = unittests.common.mock_response(do_request, response_text)
            unittests.common.bucket().put_bucket_acl(acl_defined)

            self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_get_acl(self, do_request):
        for permission in ['private', 'public-read', 'public-read-write']:
            request_text = '''GET /?acl= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:29 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:MzR4Otn9sCVJHrICSfeLBxb5Y3c='''

            response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:29 GMT
Content-Type: application/xml
Content-Length: 214
Connection: keep-alive
x-oss-request-id: 566B6BD1B1119B6F747154A3

<?xml version="1.0" encoding="UTF-8"?>
<AccessControlPolicy>
  <Owner>
    <ID>1047205513514293</ID>
    <DisplayName>1047205513514293</DisplayName>
  </Owner>
  <AccessControlList>
    <Grant>{0}</Grant>
  </AccessControlList>
</AccessControlPolicy>'''.format(permission)

            req_info = unittests.common.mock_response(do_request, response_text)
            result = unittests.common.bucket().get_bucket_acl()

            self.assertRequest(req_info, request_text)
            self.assertEqual(result.acl, permission)

    @patch('oss2.Session.do_request')
    def test_put_logging(self, do_request):
        request_text = '''PUT /?logging= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 156
date: Sat, 12 Dec 2015 00:35:42 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:uofFeeNDtRu6WY5iUkNwTymtPI4=

<BucketLoggingStatus><LoggingEnabled><TargetBucket>ming-xxx-share</TargetBucket><TargetPrefix>{0}</TargetPrefix></LoggingEnabled></BucketLoggingStatus>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:42 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BDED5A340D61A739262'''

        for prefix in [u'日志+/', 'logging/', '日志+/']:
            req_info = unittests.common.mock_response(do_request, response_text)
            unittests.common.bucket().put_bucket_logging(oss2.models.BucketLogging('ming-xxx-share', prefix))
            self.assertRequest(req_info, request_text.format(oss2.to_string(prefix)))

    @patch('oss2.Session.do_request')
    def test_delete_logging(self, do_request):
        request_text = '''DELETE /?logging= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 0
date: Sat, 12 Dec 2015 00:35:45 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:/mRx9r65GIqp9+ROsdVf1D7CupY='''

        response_text = '''HTTP/1.1 204 No Content
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:46 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BE2B713DE5875F08177'''

        req_info = unittests.common.mock_response(do_request, response_text)
        result = unittests.common.bucket().delete_bucket_logging()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BE2B713DE5875F08177')

    @patch('oss2.Session.do_request')
    def test_get_logging(self, do_request):
        request_text = '''GET /?logging= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:45 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:9J42bjaM3bgBuP0l/79K64DccZ0='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:43 GMT
Content-Type: application/xml
Content-Length: 214
Connection: keep-alive
x-oss-request-id: 566B6BDFD5A340D61A739420

<?xml version="1.0" encoding="UTF-8"?>
<BucketLoggingStatus>
  <LoggingEnabled>
    <TargetBucket>ming-xxx-share</TargetBucket>
    <TargetPrefix>{0}</TargetPrefix>
  </LoggingEnabled>
</BucketLoggingStatus>'''

        for prefix in [u'日志%+/*', 'logging/', '日志%+/*']:
            req_info = unittests.common.mock_response(do_request, response_text.format(oss2.to_string(prefix)))
            result = unittests.common.bucket().get_bucket_logging()

            self.assertRequest(req_info, request_text)
            self.assertEqual(result.target_bucket, 'ming-xxx-share')
            self.assertEqual(result.target_prefix, oss2.to_string(prefix))

    @patch('oss2.Session.do_request')
    def test_put_website(self, do_request):
        request_text = '''PUT /?website= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 155
date: Sat, 12 Dec 2015 00:35:47 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:ZUVg/fNrUVyan0Y5xhz5zvcPZcs=

<WebsiteConfiguration><IndexDocument><Suffix>{0}</Suffix></IndexDocument><ErrorDocument><Key>{1}</Key></ErrorDocument></WebsiteConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:47 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BE31BA604C27DD429E8'''

        for index, error in [('index+中文.html', 'error.中文') ,(u'中-+()文.index', u'@#$%中文.error')]:
            req_info = unittests.common.mock_response(do_request, response_text)
            unittests.common.bucket().put_bucket_website(oss2.models.BucketWebsite(index, error))

            self.assertRequest(req_info, request_text.format(oss2.to_string(index), oss2.to_string(error)))

    @patch('oss2.Session.do_request')
    def test_get_website(self, do_request):
        request_text = '''GET /?website= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:48 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:gTNIEjVmU76CwrhC2HftAaHcwBw='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:49 GMT
Content-Type: application/xml
Content-Length: 218
Connection: keep-alive
x-oss-request-id: 566B6BE5FFDB697977D52407

<?xml version="1.0" encoding="UTF-8"?>
<WebsiteConfiguration>
  <IndexDocument>
    <Suffix>{0}</Suffix>
  </IndexDocument>
  <ErrorDocument>
    <Key>{1}</Key>
  </ErrorDocument>
</WebsiteConfiguration>'''

        for index, error in [('index+中文.html', 'error.中文') ,(u'中-+()文.index', u'@#$%中文.error')]:
            req_info = unittests.common.mock_response(do_request, response_text.format(oss2.to_string(index), oss2.to_string(error)))

            result = unittests.common.bucket().get_bucket_website()

            self.assertRequest(req_info, request_text)

            self.assertEqual(result.index_file, oss2.to_string(index))
            self.assertEqual(result.error_file, oss2.to_string(error))

    @patch('oss2.Session.do_request')
    def test_delete_website(self, do_request):
        request_text = '''DELETE /?website= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 0
date: Sat, 12 Dec 2015 00:35:51 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:+oqAxH7C3crBPSg94DYaamjHbOo='''

        response_text = '''HTTP/1.1 204 No Content
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:51 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BE7B1119B6F7471769A'''

        req_info = unittests.common.mock_response(do_request, response_text)
        result = unittests.common.bucket().delete_bucket_website()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BE7B1119B6F7471769A')

    @patch('oss2.Session.do_request')
    def test_put_lifecycle_date(self, do_request):
        from oss2.models import (LifecycleExpiration, LifecycleRule, BucketLifecycle, AbortMultipartUpload,
                                StorageTransition)

        request_text = '''PUT /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 198
date: Sat, 12 Dec 2015 00:35:37 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:45HTpSD5osRvtusf8VCkmchZZFs=

<LifecycleConfiguration><Rule><ID>{0}</ID><Prefix>{1}</Prefix><Status>{2}</Status>\
<Expiration><Date>{3}</Date></Expiration><AbortMultipartUpload><CreatedBeforeDate>{5}</CreatedBeforeDate></AbortMultipartUpload>\
<Transition><StorageClass>Standard</StorageClass><CreatedBeforeDate>{4}</CreatedBeforeDate></Transition></Rule></LifecycleConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:37 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BD9B295345D15740F1F'''

        id = 'hello world'
        prefix = '中文前缀'
        status = 'Disabled'
        date = '2015-12-25T00:00:00.000Z'
        date1 = datetime.date(2015, 12, 25)

        req_info = unittests.common.mock_response(do_request, response_text)
        rule = LifecycleRule(id, prefix,
                             status=LifecycleRule.DISABLED,
                             expiration=LifecycleExpiration(date=date1),
                             storage_transitions=[StorageTransition(created_before_date=date1, storage_class=oss2.BUCKET_STORAGE_CLASS_STANDARD)],
                             abort_multipart_upload=AbortMultipartUpload(created_before_date=date1))
        unittests.common.bucket().put_bucket_lifecycle(BucketLifecycle([rule]))

        self.assertRequest(req_info, request_text.format(id, prefix, status, date, date, date))

    @patch('oss2.Session.do_request')
    def test_put_lifecycle_days(self, do_request):
        from oss2.models import (LifecycleExpiration, LifecycleRule, BucketLifecycle, AbortMultipartUpload,
                                 StorageTransition)

        request_text = '''PUT /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 178
date: Sat, 12 Dec 2015 00:35:39 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:BdIgh0100HCI1QkZKsArQvQafzY=

<LifecycleConfiguration><Rule><ID>{0}</ID><Prefix>{1}</Prefix><Status>{2}</Status>\
<Expiration><Days>{3}</Days></Expiration><AbortMultipartUpload><Days>{5}</Days></AbortMultipartUpload>\
<Transition><StorageClass>Standard</StorageClass><Days>{4}</Days></Transition></Rule></LifecycleConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:39 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BDB1BA604C27DD419B8'''

        req_info = unittests.common.mock_response(do_request, response_text)

        id = '中文ID'
        prefix = '中文前缀'
        status = 'Enabled'
        days = 3

        rule = LifecycleRule(id, prefix,
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=days),
                             storage_transitions=[StorageTransition(days=days, storage_class=oss2.BUCKET_STORAGE_CLASS_STANDARD)],
                             abort_multipart_upload=AbortMultipartUpload(days=days))

        unittests.common.bucket().put_bucket_lifecycle(BucketLifecycle([rule]))

        self.assertRequest(req_info, request_text.format(id, prefix, status, days, days, days))

    @patch('oss2.Session.do_request')
    def test_get_lifecycle_date(self, do_request):
        from oss2.models import LifecycleRule

        request_text = '''GET /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:38 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:mr0QeREuAcoeK0rSWBnobrzu6uU='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:38 GMT
Content-Type: application/xml
Content-Length: 277
Connection: keep-alive
x-oss-request-id: 566B6BDA010B7A4314D1614A

<?xml version="1.0" encoding="UTF-8"?>
<LifecycleConfiguration>
  <Rule>
    <ID>{0}</ID>
    <Prefix>{1}</Prefix>
    <Status>{2}</Status>
    <Expiration>
      <Date>{3}</Date>
    </Expiration>
  </Rule>
</LifecycleConfiguration>'''

        id = 'whatever'
        prefix = 'lifecycle rule 1'
        status = LifecycleRule.DISABLED
        date = datetime.date(2015, 12, 25)

        req_info = unittests.common.mock_response(do_request, response_text.format(id, prefix, status, '2015-12-25T00:00:00.000Z'))
        result = unittests.common.bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, date)
        self.assertEqual(rule.expiration.days, None)

        self.assertTrue(rule.tagging is None)

    @patch('oss2.Session.do_request')
    def test_get_lifecycle_days(self, do_request):
        from oss2.models import LifecycleRule

        request_text = '''GET /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:39 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:MFggWRq+dzUx2qdEuIeyrJTct1I='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:39 GMT
Content-Type: application/xml
Content-Length: 243
Connection: keep-alive
x-oss-request-id: 566B6BDB1BA604C27DD419B0

<?xml version="1.0" encoding="UTF-8"?>
<LifecycleConfiguration>
  <Rule>
    <ID>{0}</ID>
    <Prefix>{1}</Prefix>
    <Status>{2}</Status>
    <Expiration>
      <Days>{3}</Days>
    </Expiration>
  </Rule>
</LifecycleConfiguration>'''

        id = '1-2-3'
        prefix = '中+-*%^$#@!文'
        status = LifecycleRule.ENABLED
        days = 356

        req_info = unittests.common.mock_response(do_request, response_text.format(id, prefix, status, days))
        result = unittests.common.bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, None)
        self.assertEqual(rule.expiration.days, days)

        self.assertTrue(rule.tagging is None)

    @patch('oss2.Session.do_request')
    def test_get_lifecycle_storage_transition(self, do_request):
        from oss2.models import LifecycleRule

        request_text = '''GET /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:38 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:mr0QeREuAcoeK0rSWBnobrzu6uU='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:38 GMT
Content-Type: application/xml
Content-Length: 277
Connection: keep-alive
x-oss-request-id: 566B6BDA010B7A4314D1614A

<?xml version="1.0" encoding="UTF-8"?>
<LifecycleConfiguration>
  <Rule>
    <ID>{0}</ID>
    <Prefix>{1}</Prefix>
    <Status>{2}</Status>
    <Transition>
        <Days>10</Days>
        <StorageClass>Standard</StorageClass>
    </Transition>
    <Transition>
        <Days>20</Days>
        <StorageClass>IA</StorageClass>
    </Transition>
    <Transition>
        <CreatedBeforeDate>{3}</CreatedBeforeDate>
        <StorageClass>Archive</StorageClass>
    </Transition>
  </Rule>
</LifecycleConfiguration>'''

        id = 'whatever'
        prefix = 'lifecycle rule 1'
        status = LifecycleRule.DISABLED
        date = '2015-12-25T00:00:00.000Z'
        date1 = datetime.date(2015, 12, 25)

        req_info = unittests.common.mock_response(do_request, response_text.format(id, prefix, status, date))
        result = unittests.common.bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(len(rule.storage_transitions), 3)
        self.assertEqual(rule.storage_transitions[0].days, 10)
        self.assertEqual(rule.storage_transitions[0].storage_class, oss2.BUCKET_STORAGE_CLASS_STANDARD)
        self.assertEqual(rule.storage_transitions[1].days, 20)
        self.assertEqual(rule.storage_transitions[1].storage_class, oss2.BUCKET_STORAGE_CLASS_IA)
        self.assertEqual(rule.storage_transitions[2].created_before_date, date1)
        self.assertEqual(rule.storage_transitions[2].storage_class, oss2.BUCKET_STORAGE_CLASS_ARCHIVE)

        self.assertTrue(rule.tagging is None)

    @patch('oss2.Session.do_request')
    def test_get_lifecycle_abort_multipart_days(self, do_request):
        from oss2.models import LifecycleRule

        request_text = '''GET /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:38 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:mr0QeREuAcoeK0rSWBnobrzu6uU='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:38 GMT
Content-Type: application/xml
Content-Length: 277
Connection: keep-alive
x-oss-request-id: 566B6BDA010B7A4314D1614A

<?xml version="1.0" encoding="UTF-8"?>
<LifecycleConfiguration>
  <Rule>
    <ID>{0}</ID>
    <Prefix>{1}</Prefix>
    <Status>{2}</Status>
    <AbortMultipartUpload>
      <Days>{3}</Days>
    </AbortMultipartUpload>
  </Rule>
</LifecycleConfiguration>'''

        id = 'whatever'
        prefix = 'lifecycle rule 1'
        status = LifecycleRule.DISABLED
        days = 10

        req_info = unittests.common.mock_response(do_request, response_text.format(id, prefix, status, days))
        result = unittests.common.bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.abort_multipart_upload.days, days)

    @patch('oss2.Session.do_request')
    def test_get_lifecycle_abort_multipart_date(self, do_request):
        from oss2.models import LifecycleRule

        request_text = '''GET /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:38 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:mr0QeREuAcoeK0rSWBnobrzu6uU='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:38 GMT
Content-Type: application/xml
Content-Length: 277
Connection: keep-alive
x-oss-request-id: 566B6BDA010B7A4314D1614A

<?xml version="1.0" encoding="UTF-8"?>
<LifecycleConfiguration>
  <Rule>
    <ID>{0}</ID>
    <Prefix>{1}</Prefix>
    <Status>{2}</Status>
    <AbortMultipartUpload>
      <CreatedBeforeDate>{3}</CreatedBeforeDate>
    </AbortMultipartUpload>
  </Rule>
</LifecycleConfiguration>'''

        id = 'whatever'
        prefix = 'lifecycle rule 1'
        status = LifecycleRule.DISABLED
        date = '2015-12-25T00:00:00.000Z'
        date1 = datetime.date(2015, 12, 25)

        req_info = unittests.common.mock_response(do_request, response_text.format(id, prefix, status, date))
        result = unittests.common.bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.abort_multipart_upload.created_before_date, date1)

    @patch('oss2.Session.do_request')
    def test_get_lifecycle_tagging(self, do_request):
        from oss2.models import LifecycleRule

        request_text = '''GET /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:38 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:mr0QeREuAcoeK0rSWBnobrzu6uU='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:38 GMT
Content-Type: application/xml
Content-Length: 277
Connection: keep-alive
x-oss-request-id: 566B6BDA010B7A4314D1614A

<?xml version="1.0" encoding="UTF-8"?>
<LifecycleConfiguration>
  <Rule>
    <ID>{0}</ID>
    <Prefix>{1}</Prefix>
    <Status>{2}</Status>
    <Tag><Key>k1</Key><Value>v1</Value></Tag>
    <Tag><Key>k2</Key><Value>v2</Value></Tag>
    <Tag><Key>k3</Key><Value>v3</Value></Tag>
    <Expiration>
      <Date>{3}</Date>
    </Expiration>
  </Rule>
</LifecycleConfiguration>'''

        id = 'whatever'
        prefix = 'lifecycle rule 1'
        status = LifecycleRule.DISABLED
        date = datetime.date(2015, 12, 25)

        req_info = unittests.common.mock_response(do_request, response_text.format(id, prefix, status, '2015-12-25T00:00:00.000Z'))
        result = unittests.common.bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, date)
        self.assertEqual(rule.expiration.days, None)

        tagging_rule = rule.tagging.tag_set.tagging_rule
        self.assertEqual(3, rule.tagging.tag_set.len())
        self.assertEqual('v1', tagging_rule['k1'])
        self.assertEqual('v2', tagging_rule['k2'])
        self.assertEqual('v3', tagging_rule['k3'])

    @patch('oss2.Session.do_request')
    def test_get_stat(self, do_request):
        request_text = '''GET /?stat HTTP/1.1
Host: sbowspxjhmccpmesjqcwagfw.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:37:17 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:wopWcmMd/70eNKYOc9M6ZA21yY8='''

        response_text = '''HTTP/1.1 403
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:37:17 GMT
Content-Type: application/xml
Content-Length: 287
Connection: keep-alive
x-oss-request-id: 566B6C3D6086505A0CFF0F68

<?xml version="1.0" encoding="UTF-8"?>
<Error>
  <Code>AccessDenied</Code>
  <Message>AccessDenied</Message>
  <RequestId>566B6C3D6086505A0CFF0F68</RequestId>
  <HostId>sbowspxjhmccpmesjqcwagfw.oss-cn-hangzhou.aliyuncs.com</HostId>
</Error>'''

        req_info = unittests.common.mock_response(do_request, response_text)
        bucket = unittests.common.bucket()
        bucket.bucket_name = 'sbowspxjhmccpmesjqcwagfw'
        self.assertRaises(oss2.exceptions.AccessDenied, bucket.get_bucket_stat)
        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_delete_lifecycle(self, do_request):
        request_text = '''DELETE /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 0
date: Sat, 12 Dec 2015 00:35:41 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:4YLmuuI4dwa3tYTVPqHqHrul/5s='''

        response_text = '''HTTP/1.1 204 No Content
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:41 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BDD770DFE490473A0F1'''

        req_info = unittests.common.mock_response(do_request, response_text)
        result = unittests.common.bucket().delete_bucket_lifecycle()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BDD770DFE490473A0F1')

    @patch('oss2.Session.do_request')
    def test_put_cors(self, do_request):
        import xml.etree.ElementTree as ElementTree

        request_text = '''PUT /?cors= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 228
date: Sat, 12 Dec 2015 00:35:35 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:cmWZPrAca3p4IZaAc3iqJoQEzNw=

<CORSConfiguration><CORSRule><AllowedOrigin>*</AllowedOrigin><AllowedMethod>HEAD</AllowedMethod><AllowedMethod>GET</AllowedMethod><AllowedHeader>*</AllowedHeader><MaxAgeSeconds>1000</MaxAgeSeconds></CORSRule></CORSConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:35 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BD7D9816D686F72A86A'''

        req_info = unittests.common.mock_response(do_request, response_text)

        rule = oss2.models.CorsRule(allowed_origins=['*'],
                                    allowed_methods=['HEAD', 'GET'],
                                    allowed_headers=['*'],
                                    max_age_seconds=1000)

        unittests.common.bucket().put_bucket_cors(oss2.models.BucketCors([rule]))

        self.assertRequest(req_info ,request_text)

        root = ElementTree.fromstring(req_info.data)
        rule_node = root.find('CORSRule')

        self.assertSortedListEqual(rule.allowed_origins, all_tags(rule_node, 'AllowedOrigin'))
        self.assertSortedListEqual(rule.allowed_methods, all_tags(rule_node, 'AllowedMethod'))
        self.assertSortedListEqual(rule.allowed_headers, all_tags(rule_node, 'AllowedHeader'))

        self.assertEqual(rule.max_age_seconds, int(rule_node.find('MaxAgeSeconds').text))

    @patch('oss2.Session.do_request')
    def test_get_cors(self, do_request):
        request_text = '''GET /?cors= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:37 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:wfV1/6+sVdNzsXbHEXZQeQRC7xk='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:37 GMT
Content-Type: application/xml
Content-Length: 300
Connection: keep-alive
x-oss-request-id: 566B6BD927A4046E9C725566

<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration>
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

        req_info = unittests.common.mock_response(do_request, response_text)

        rules = unittests.common.bucket().get_bucket_cors().rules

        self.assertRequest(req_info, request_text)

        self.assertEqual(rules[0].allowed_origins, ['*'])
        self.assertEqual(rules[0].allowed_methods, ['PUT', 'GET'])
        self.assertEqual(rules[0].allowed_headers, ['Authorization'])

        self.assertEqual(rules[1].allowed_origins, ['http://www.a.com', 'www.b.com'])
        self.assertEqual(rules[1].allowed_methods, ['GET'])
        self.assertEqual(rules[1].expose_headers, ['x-oss-test', 'x-oss-test1'])
        self.assertEqual(rules[1].max_age_seconds, 100)

    @patch('oss2.Session.do_request')
    def test_delete_cors(self, do_request):
        request_text = '''DELETE /?cors= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 0
date: Sat, 12 Dec 2015 00:35:37 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:C8A0N4wRk71Xxh1Fc88BnhBvaxw='''

        response_text = '''HTTP/1.1 204 No Content
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:37 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BD927A4046E9C725578'''

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().delete_bucket_cors()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')

    @patch('oss2.Session.do_request')
    def test_put_referer(self, do_request):
        from oss2.models import BucketReferer

        request_text = '''PUT /?referer= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 249
date: Sat, 12 Dec 2015 00:35:46 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Kq2RS9nmT44C1opXGbcLzNdTt1A=

<RefererConfiguration><AllowEmptyReferer>true</AllowEmptyReferer><RefererList><Referer>http://hello.com</Referer><Referer>mibrowser:home</Referer><Referer>{0}</Referer></RefererList></RefererConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:46 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BE244ABFA2608E5A8AD'''

        req_info = unittests.common.mock_response(do_request, response_text)

        unittests.common.bucket().put_bucket_referer(BucketReferer(True, ['http://hello.com', 'mibrowser:home', '阿里巴巴']))

        self.assertRequest(req_info, request_text.format('阿里巴巴'))

    @patch('oss2.Session.do_request')
    def test_get_referer(self, do_request):
        request_text = '''GET /?referer= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:47 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:nWqS3JExf/lsVxm+Sbxbg2cQyrc='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:47 GMT
Content-Type: application/xml
Content-Length: 319
Connection: keep-alive
x-oss-request-id: 566B6BE3BCD1D4FE65D449A2

<?xml version="1.0" encoding="UTF-8"?>
<RefererConfiguration>
  <AllowEmptyReferer>true</AllowEmptyReferer>
  <RefererList>
    <Referer>http://hello.com</Referer>
    <Referer>mibrowser:home</Referer>
    <Referer>{0}</Referer>
  </RefererList>
</RefererConfiguration>'''.format('阿里巴巴')

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().get_bucket_referer()

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.allow_empty_referer, True)
        self.assertSortedListEqual(result.referers, ['http://hello.com', 'mibrowser:home', '阿里巴巴'])

    @patch('oss2.Session.do_request')
    def test_get_location(self, do_request):
        request_text = '''GET /?location= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:41 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Pt0DtPQ/FODOGs5y0yTIVctRcok='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:42 GMT
Content-Type: application/xml
Content-Length: 96
Connection: keep-alive
x-oss-request-id: 566B6BDD68248CE14F729DC0

<?xml version="1.0" encoding="UTF-8"?>
<LocationConstraint>oss-cn-hangzhou</LocationConstraint>'''

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().get_bucket_location()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.location, 'oss-cn-hangzhou')

    @patch('oss2.Session.do_request')
    def test_create_live_channel(self, do_request):
        request_text = '''PUT /lc?live= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Accept: */*
User-Agent: aliyun-sdk-python/2.1.1(Windows/7/AMD64;2.7.10)
date: Tue, 09 Aug 2016 11:25:01 GMT
authorization: OSS 2NeLUvmJFYbrj2Eb:ljTfGW1yYoTGQN7Tl9gU36kJcxQ=
Content-Length: 217

<LiveChannelConfiguration><Description /><Status>enabled</Status><Target><Type>HLS</Type><FragDuration>5</FragDuration><FragCount>3</FragCount><PlaylistName>test.m3u8</PlaylistName></Target></LiveChannelConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Tue, 09 Aug 2016 11:25:01 GMT
Content-Type: application/xml
Content-Length: 437
Connection: keep-alive
x-oss-request-id: 57A9BD8D2FADF35D13CD7E5E
x-oss-server-time: 118

<?xml version="1.0" encoding="UTF-8"?>
<CreateLiveChannelResult>
  <PublishUrls>
    <Url>rtmp://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/live/lc</Url>
  </PublishUrls>
  <PlayUrls>
    <Url>http://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/lc/test.m3u8</Url>
  </PlayUrls>
</CreateLiveChannelResult>'''

        req_info = unittests.common.mock_response(do_request, response_text)

        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name="test.m3u8")
        channel_info = oss2.models.LiveChannelInfo(target=channel_target)
        unittests.common.bucket().create_live_channel("lc", channel_info)
        
        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_list_live_channel(self, do_request):
        from oss2.utils import iso8601_to_unixtime
        
        request_text = '''GET /?live= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Accept: */*
User-Agent: aliyun-sdk-python/2.1.1(Windows/7/AMD64;2.7.10)
date: Tue, 09 Aug 2016 11:51:30 GMT
authorization: OSS 2NeLUvmJFYbrj2Eb:BQCNOYdGglcAbhdHhqTfVNtLBow='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Tue, 09 Aug 2016 11:51:30 GMT
Content-Type: application/xml
Content-Length: 100
Connection: keep-alive
x-oss-request-id: 57A9C3C27FBF67E9BE686908
x-oss-server-time: 1

<?xml version="1.0" encoding="UTF-8"?>
<ListLiveChannelResult>
  <Prefix>test</Prefix>
  <Marker></Marker>
  <MaxKeys>2</MaxKeys>
  <IsTruncated>true</IsTruncated>
  <NextMarker>test3</NextMarker>
  <LiveChannel>
    <Name>test1</Name>
    <Description>test1</Description>
    <Status>enabled</Status>
    <LastModified>2016-04-01T07:04:00.000Z</LastModified>
    <PublishUrls>
      <Url>rtmp://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/live/test1</Url>
    </PublishUrls>
    <PlayUrls>
      <Url>http://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/test1/playlist.m3u8</Url>
    </PlayUrls>
  </LiveChannel>
  <LiveChannel>
    <Name>test2</Name>
    <Description>test2</Description>
    <Status>disabled</Status>
    <LastModified>2016-04-01T08:04:50.000Z</LastModified>
    <PublishUrls>
      <Url>rtmp://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/live/test2</Url>
    </PublishUrls>
    <PlayUrls>
      <Url>http://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/test2/playlist.m3u8</Url>
    </PlayUrls>
  </LiveChannel>
</ListLiveChannelResult>'''

        req_info = unittests.common.mock_response(do_request, response_text)
        result = unittests.common.bucket().list_live_channel('test', '', 2)
        self.assertRequest(req_info, request_text)
        
        self.assertEqual(result.prefix, 'test')
        self.assertEqual(result.marker, '')
        self.assertEqual(result.max_keys, 2)
        self.assertEqual(result.is_truncated, True)
        self.assertEqual(result.next_marker, 'test3')
        self.assertEqual(len(result.channels), 2)
        self.assertEqual(result.channels[0].name, 'test1')
        self.assertEqual(result.channels[0].description, 'test1')
        self.assertEqual(result.channels[0].status, 'enabled')
        self.assertEqual(result.channels[0].last_modified, iso8601_to_unixtime('2016-04-01T07:04:00.000Z'))
        self.assertEqual(result.channels[0].publish_url, 'rtmp://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/live/test1')
        self.assertEqual(result.channels[0].play_url, 'http://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/test1/playlist.m3u8')
        self.assertEqual(result.channels[1].name, 'test2')
        self.assertEqual(result.channels[1].description, 'test2')
        self.assertEqual(result.channels[1].status, 'disabled')
        self.assertEqual(result.channels[1].last_modified, iso8601_to_unixtime('2016-04-01T08:04:50.000Z'))
        self.assertEqual(result.channels[1].publish_url, 'rtmp://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/live/test2')
        self.assertEqual(result.channels[1].play_url, 'http://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/test2/playlist.m3u8')

    @patch('oss2.Session.do_request')
    def test_get_live_channel_stat(self, do_request):
        from oss2.utils import iso8601_to_unixtime
        from oss2.models import LiveChannelAudioStat, LiveChannelVideoStat
        
        request_text = '''GET /lc?comp=stat&live= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Accept: */*
User-Agent: aliyun-sdk-python/2.1.1(Windows/7/AMD64;2.7.10)
date: Tue, 09 Aug 2016 11:51:30 GMT
authorization: OSS 2NeLUvmJFYbrj2Eb:BQCNOYdGglcAbhdHhqTfVNtLBow='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Tue, 09 Aug 2016 11:51:30 GMT
Content-Type: application/xml
Content-Length: 100
Connection: keep-alive
x-oss-request-id: 57A9C3C27FBF67E9BE686908
x-oss-server-time: 1

<?xml version="1.0" encoding="UTF-8"?>
<LiveChannelStat>
  <Status>Live</Status>
  <ConnectedTime>2016-08-08T05:59:28.000Z</ConnectedTime>
  <RemoteAddr>8.8.8.8:57186</RemoteAddr>
  <Video>
    <Width>1280</Width>
    <Height>536</Height>
    <FrameRate>24</FrameRate>
    <Bandwidth>214146</Bandwidth>
    <Codec>H264</Codec>
  </Video>
  <Audio>
    <Bandwidth>11444</Bandwidth>
    <SampleRate>22050</SampleRate>
    <Codec>AAC</Codec>
  </Audio>
</LiveChannelStat>
'''

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().get_live_channel_stat('lc')
        
        self.assertRequest(req_info, request_text)
        self.assertEqual(result.status, 'Live')
        self.assertEqual(result.connected_time, iso8601_to_unixtime('2016-08-08T05:59:28.000Z'))
        self.assertEqual(result.remote_addr, '8.8.8.8:57186')
        video = LiveChannelVideoStat(1280, 536, 24, 'H264', 214146)
        self.assertEqual(result.video.bandwidth, video.bandwidth)
        self.assertEqual(result.video.codec, video.codec)
        self.assertEqual(result.video.frame_rate, video.frame_rate)
        self.assertEqual(result.video.height, video.height)
        self.assertEqual(result.video.width, video.width)
        audio = LiveChannelAudioStat('AAC', 22050, 11444)
        self.assertEqual(result.audio.bandwidth, audio.bandwidth)
        self.assertEqual(result.audio.codec, audio.codec)
        self.assertEqual(result.audio.sample_rate, audio.sample_rate)

    @patch('oss2.Session.do_request')
    def test_get_live_channel_history(self, do_request):
        from oss2.models import LiveRecord
        from oss2.utils import iso8601_to_unixtime
                
        request_text = '''GET /lc?comp=history&live= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Accept: */*
User-Agent: aliyun-sdk-python/2.1.1(Windows/7/AMD64;2.7.10)
date: Tue, 09 Aug 2016 12:24:13 GMT
authorization: OSS 2NeLUvmJFYbrj2Eb:j9Fb7RinrXTyyX7FKtP5QAK0FZs='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Tue, 09 Aug 2016 12:24:13 GMT
Content-Type: application/xml
Content-Length: 62
Connection: keep-alive
x-oss-request-id: 57A9CB6DF3D45CE477C0227B
x-oss-server-time: 1

<?xml version="1.0" encoding="UTF-8"?>
<LiveChannelHistory>
  <LiveRecord>
    <StartTime>2016-08-06T05:59:28.000Z</StartTime>
    <EndTime>2016-08-06T06:02:43.000Z</EndTime>
    <RemoteAddr>8.8.8.8:57186</RemoteAddr>
  </LiveRecord>
  <LiveRecord>
    <StartTime>2016-08-06T06:16:20.000Z</StartTime>
    <EndTime>2016-08-06T06:16:25.000Z</EndTime>
    <RemoteAddr>1.1.1.1:57365</RemoteAddr>
  </LiveRecord>
</LiveChannelHistory>
'''

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().get_live_channel_history('lc')
        
        self.assertRequest(req_info, request_text)
        self.assertEqual(len(result.records), 2)
        lr = LiveRecord(iso8601_to_unixtime('2016-08-06T05:59:28.000Z'),
                        iso8601_to_unixtime('2016-08-06T06:02:43.000Z'),
                        '8.8.8.8:57186')
        self.assertEqual(result.records[0].start_time, lr.start_time)
        self.assertEqual(result.records[0].end_time, lr.end_time)
        self.assertEqual(result.records[0].remote_addr, lr.remote_addr)
        lr = LiveRecord(iso8601_to_unixtime('2016-08-06T06:16:20.000Z'), 
                        iso8601_to_unixtime('2016-08-06T06:16:25.000Z'),
                        '1.1.1.1:57365')
        self.assertEqual(result.records[1].start_time, lr.start_time)
        self.assertEqual(result.records[1].end_time, lr.end_time)
        self.assertEqual(result.records[1].remote_addr, lr.remote_addr)

    @patch('oss2.Session.do_request')
    def test_post_vod_playlist(self, do_request):                
        request_text = '''POST /lc%2Ftest.m3u8?vod=&endTime=1470792140&startTime=1470788540 HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Accept: */*
User-Agent: aliyun-sdk-python/2.1.1(Windows/7/AMD64;2.7.10)
date: Wed, 10 Aug 2016 01:23:20 GMT
authorization: OSS 2NeLUvmJFYbrj2Eb:OifxZSHuzeR/Lp3hFJAqBw3VNy8=
Content-Length: 0'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Wed, 06 Apr 2016 06:00:21 GMT
Content-Length: 0
Content-Type: application/xml
Connection: keep-alive
x-oss-request-id: 5704A5F5B9247571DF000031
x-oss-server-time: 21
'''

        req_info = unittests.common.mock_response(do_request, response_text)
        
        unittests.common.bucket().post_vod_playlist('lc', 'test.m3u8', 1470788540, 1470792140)
        self.assertRequest(req_info, request_text)


if __name__ == '__main__':
    unittest.main()
    
