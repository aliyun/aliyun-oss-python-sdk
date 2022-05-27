# -*- coding: utf-8 -*-

import datetime

from mock import patch
from functools import partial

from oss2 import to_string
from oss2.models import AggregationsRequest, MetaQuery
from unittests.common import *


def all_tags(parent, tag):
    return [to_string(node.text) or '' for node in parent.findall(tag)]


class TestBucket(OssTestCase):
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

        req_info = mock_response(do_request, response_text)
        bucket().create_bucket(oss2.BUCKET_ACL_PRIVATE)

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

            req_info = mock_response(do_request, response_text)
            bucket().put_bucket_acl(acl_defined)

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

            req_info = mock_response(do_request, response_text)
            result = bucket().get_bucket_acl()

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
            req_info = mock_response(do_request, response_text)
            bucket().put_bucket_logging(oss2.models.BucketLogging('ming-xxx-share', prefix))
            self.assertRequest(req_info, request_text.format(to_string(prefix)))

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

        req_info = mock_response(do_request, response_text)
        result = bucket().delete_bucket_logging()

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
            req_info = mock_response(do_request, response_text.format(to_string(prefix)))
            result = bucket().get_bucket_logging()

            self.assertRequest(req_info, request_text)
            self.assertEqual(result.target_bucket, 'ming-xxx-share')
            self.assertEqual(result.target_prefix, to_string(prefix))

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
            req_info = mock_response(do_request, response_text)
            bucket().put_bucket_website(oss2.models.BucketWebsite(index, error))

            self.assertRequest(req_info, request_text.format(to_string(index), to_string(error)))

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
            req_info = mock_response(do_request, response_text.format(to_string(index), to_string(error)))

            result = bucket().get_bucket_website()

            self.assertRequest(req_info, request_text)

            self.assertEqual(result.index_file, to_string(index))
            self.assertEqual(result.error_file, to_string(error))

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

        req_info = mock_response(do_request, response_text)
        result = bucket().delete_bucket_website()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BE7B1119B6F7471769A')

    @patch('oss2.Session.do_request')
    def test_put_lifecycle_date(self, do_request):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        request_text = '''PUT /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 198
date: Sat, 12 Dec 2015 00:35:37 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:45HTpSD5osRvtusf8VCkmchZZFs=

<LifecycleConfiguration><Rule><ID>{0}</ID><Prefix>{1}</Prefix><Status>{2}</Status><Expiration><Date>{3}</Date></Expiration></Rule></LifecycleConfiguration>'''

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

        req_info = mock_response(do_request, response_text)
        rule = LifecycleRule(id, prefix,
                             status=LifecycleRule.DISABLED,
                             expiration=LifecycleExpiration(date=datetime.date(2015, 12, 25)))
        bucket().put_bucket_lifecycle(BucketLifecycle([rule]))

        self.assertRequest(req_info, request_text.format(id, prefix, status, date))

    @patch('oss2.Session.do_request')
    def test_put_lifecycle_days(self, do_request):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        request_text = '''PUT /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 178
date: Sat, 12 Dec 2015 00:35:39 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:BdIgh0100HCI1QkZKsArQvQafzY=

<LifecycleConfiguration><Rule><ID>{0}</ID><Prefix>{1}</Prefix><Status>{2}</Status><Expiration><Days>{3}</Days></Expiration></Rule></LifecycleConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:39 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BDB1BA604C27DD419B8'''

        req_info = mock_response(do_request, response_text)

        id = '中文ID'
        prefix = '中文前缀'
        status = 'Enabled'
        days = 3

        rule = LifecycleRule(id, prefix,
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=days))
        bucket().put_bucket_lifecycle(BucketLifecycle([rule]))

        self.assertRequest(req_info, request_text.format(id, prefix, status, days))

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

        req_info = mock_response(do_request, response_text.format(id, prefix, status, '2015-12-25T00:00:00.000Z'))
        result = bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, date)
        self.assertEqual(rule.expiration.days, None)

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

        req_info = mock_response(do_request, response_text.format(id, prefix, status, days))
        result = bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, None)
        self.assertEqual(rule.expiration.days, days)

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

        req_info = mock_response(do_request, response_text)
        result = bucket().delete_bucket_lifecycle()

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

        req_info = mock_response(do_request, response_text)

        rule = oss2.models.CorsRule(allowed_origins=['*'],
                                    allowed_methods=['HEAD', 'GET'],
                                    allowed_headers=['*'],
                                    max_age_seconds=1000)

        bucket().put_bucket_cors(oss2.models.BucketCors([rule]))

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

        req_info = mock_response(do_request, response_text)

        rules = bucket().get_bucket_cors().rules

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

        req_info = mock_response(do_request, response_text)

        result = bucket().delete_bucket_cors()

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

        req_info = mock_response(do_request, response_text)

        bucket().put_bucket_referer(BucketReferer(True, ['http://hello.com', 'mibrowser:home', '阿里巴巴']))

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

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_referer()

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

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_location()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.location, 'oss-cn-hangzhou')

    @patch('oss2.Session.do_request')
    def test_get_stat(self, do_request):
        request_text = '''GET /?stat= HTTP/1.1
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
<BucketStat> 
    <Storage>472594058</Storage> 
    <ObjectCount>666</ObjectCount> 
    <MultipartUploadCount>992</MultipartUploadCount> 
</BucketStat>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_stat()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.storage_size_in_bytes, 472594058)
        self.assertEqual(result.object_count, 666)
        self.assertEqual(result.multi_part_upload_count, 992)

    @patch('oss2.Session.do_request')
    def test_get_stat_all_param(self, do_request):
        request_text = '''GET /?stat= HTTP/1.1
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
<BucketStat> 
    <Storage>472594058</Storage> 
    <ObjectCount>666</ObjectCount> 
    <MultipartUploadCount>992</MultipartUploadCount>
    <LiveChannelCount>4</LiveChannelCount>
    <LastModifiedTime>0</LastModifiedTime>
    <StandardStorage>430</StandardStorage>
    <StandardObjectCount>66</StandardObjectCount>
    <InfrequentAccessStorage>2359296</InfrequentAccessStorage>
    <InfrequentAccessRealStorage>360</InfrequentAccessRealStorage>
    <InfrequentAccessObjectCount>54</InfrequentAccessObjectCount>
    <ArchiveStorage>2949120</ArchiveStorage>
    <ArchiveRealStorage>450</ArchiveRealStorage>
    <ArchiveObjectCount>74</ArchiveObjectCount>
    <ColdArchiveStorage>2359296</ColdArchiveStorage>
    <ColdArchiveRealStorage>360</ColdArchiveRealStorage>
    <ColdArchiveObjectCount>36</ColdArchiveObjectCount>
</BucketStat>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_stat()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.storage_size_in_bytes, 472594058)
        self.assertEqual(result.object_count, 666)
        self.assertEqual(result.multi_part_upload_count, 992)
        self.assertEqual(result.live_channel_count, 4)
        self.assertEqual(result.last_modified_time, 0)
        self.assertEqual(result.standard_storage, 430)
        self.assertEqual(result.standard_object_count, 66)
        self.assertEqual(result.infrequent_access_storage, 2359296)
        self.assertEqual(result.infrequent_access_real_storage, 360)
        self.assertEqual(result.infrequent_access_object_count, 54)
        self.assertEqual(result.archive_storage, 2949120)
        self.assertEqual(result.archive_real_storage, 450)
        self.assertEqual(result.archive_object_count, 74)
        self.assertEqual(result.cold_archive_storage, 2359296)
        self.assertEqual(result.cold_archive_real_storage, 360)
        self.assertEqual(result.cold_archive_object_count, 36)


    @patch('oss2.Session.do_request')
    def test_get_bucket_policy(self, do_request):
        request_text = '''GET /?policy= HTTP/1.1
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
Content-Type: application/json
Content-Length: 96
Connection: keep-alive
x-oss-request-id: 566B6BDD68248CE14F729DC0

{"Version":"1","Statement":[]}
'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_policy()

        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_put_bucket_policy(self, do_request):
        request_text = '''PUT /?policy= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:41 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Pt0DtPQ/FODOGs5y0yTIVctRcok=

{"Version":"1","Statement":[]}'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:42 GMT
Content-Type: application/xml
Content-Length: 96
Connection: keep-alive
x-oss-request-id: 566B6BDD68248CE14F729DC0
'''

        req_info = mock_response(do_request, response_text)

        policy = '{"Version":"1","Statement":[]}'
        result = bucket().put_bucket_policy(policy)

        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_delete_bucket_policy(self, do_request):
        request_text = '''DELETE /?policy= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:41 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Pt0DtPQ/FODOGs5y0yTIVctRcok='''

        response_text = '''HTTP/1.1 204 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:42 GMT
Content-Type: application/xml
Content-Length: 96
Connection: keep-alive
x-oss-request-id: 566B6BDD68248CE14F729DC0
'''

        req_info = mock_response(do_request, response_text)

        result = bucket().delete_bucket_policy()

        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_put_bucket_transfer_acceleration(self, do_request):
        request_text = '''PUT /?transferAcceleration HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<?xml version="1.0" encoding="UTF-8"?>
<TransferAccelerationConfiguration><Enabled>true</Enabled>
</TransferAccelerationConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 534B371674A4D890****
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length: 443
Connection: keep-alive
Server: AliyunOSS'''

        req_info = mock_response(do_request, response_text)

        result = bucket().put_bucket_transfer_acceleration('true')

        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_get_bucket_transfer_acceleration(self, do_request):
        request_text = '''GET /?transferAcceleration HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 534B371674E88A4D8906****
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<TransferAccelerationConfiguration>
 <Enabled>true</Enabled>
</TransferAccelerationConfiguration>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_transfer_acceleration()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.enabled, 'true')

    @patch('oss2.Session.do_request')
    def test_create_bucket_cname_token(self, do_request):
        request_text = '''POST /?cname&comp=token HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<BucketCnameConfiguration><Cname><Domain>example.com</Domain></Cname></BucketCnameConfiguration>
'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<CnameToken>
  <Bucket>mybucket</Bucket>
  <Cname>example.com</Cname>;
  <Token>be1d49d863dea9ffeff3df7d6455****</Token>
  <ExpireTime>Wed, 23 Feb 2022 21:39:42 GMT</ExpireTime>
</CnameToken>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().create_bucket_cname_token('example.com')

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.bucket, 'mybucket')
        self.assertEqual(result.cname, 'example.com')
        self.assertEqual(result.token, 'be1d49d863dea9ffeff3df7d6455****')
        self.assertEqual(result.expire_time, 'Wed, 23 Feb 2022 21:39:42 GMT')

    @patch('oss2.Session.do_request')
    def test_get_bucket_cname_token(self, do_request):
        request_text = '''GET /?comp=token&cname=example.com HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<CnameToken>
  <Bucket>mybucket</Bucket>
  <Cname>example.com</Cname>;
  <Token>be1d49d863dea9ffeff3df7d6455****</Token>
  <ExpireTime>Wed, 23 Feb 2022 21:39:42 GMT</ExpireTime>
</CnameToken>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_cname_token('example.com')

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.bucket, 'mybucket')
        self.assertEqual(result.cname, 'example.com')
        self.assertEqual(result.token, 'be1d49d863dea9ffeff3df7d6455****')
        self.assertEqual(result.expire_time, 'Wed, 23 Feb 2022 21:39:42 GMT')

    @patch('oss2.Session.do_request')
    def test_put_bucket_cname(self, do_request):
        request_text = '''POST /?cname&comp=add HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<BucketCnameConfiguration>
<Cname>
<Domain>{0}</Domain>
<CertificateConfiguration>
<CertId>{1}</CertId>
<Certificate>{2}</Certificate>
<PrivateKey>{3}</PrivateKey>
<PreviousCertId>493****-cn-hangzhou</PreviousCertId>
<Force>True</Force>
<DeleteCertificate>True</DeleteCertificate>
</CertificateConfiguration>
</Cname>
</BucketCnameConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)
        domain = 'example.com'
        cert_id = '493****-cn-hangzhou'
        certificate = '-----BEGIN CERTIFICATE----- MIIDhDCCAmwCCQCFs8ixARsyrDANBgkqhkiG9w0BAQsFADCBgzELMAkGA1UEBhMC **** -----END CERTIFICATE-----'
        private_key = '-----BEGIN CERTIFICATE----- MIIDhDCCAmwCCQCFs8ixARsyrDANBgkqhkiG9w0BAQsFADCBgzELMAkGA1UEBhMC **** -----END CERTIFICATE-----'
        cert = oss2.models.CertInfo(cert_id, certificate, private_key, '493****-cn-hangzhou', True, True)
        input = oss2.models.PutBucketCnameRequest(domain, cert)
        bucket().put_bucket_cname(input)
        self.assertRequest(req_info, request_text.format(to_string(domain), to_string(cert_id), to_string(certificate), to_string(private_key)))

    @patch('oss2.Session.do_request')
    def test_list_bucket_cname(self, do_request):
        request_text = '''GET /?cname HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<ListCnameResult>
  <Bucket>targetbucket</Bucket>
  <Owner>testowner</Owner>
  <Cname>
    <Domain>example.com</Domain>
    <LastModified>2021-09-15T02:35:07.000Z</LastModified>
    <Status>Enabled</Status>
    <Certificate>
      <Type>CAS</Type>
      <CertId>493****-cn-hangzhou</CertId>
      <Status>Enabled</Status>
      <CreationDate>Wed, 15 Sep 2021 02:35:06 GMT</CreationDate>
      <Fingerprint>DE:01:CF:EC:7C:A7:98:CB:D8:6E:FB:1D:97:EB:A9:64:1D:4E:**:**</Fingerprint>
      <ValidStartDate>Tues, 12 Apr 2021 10:14:51 GMT</ValidStartDate>
      <ValidEndDate>Mon, 4 May 2048 10:14:51 GMT</ValidEndDate>
    </Certificate>
  </Cname>
  <Cname>
    <Domain>example.org</Domain>
    <LastModified>2021-09-15T02:34:58.000Z</LastModified>
    <Status>Enabled</Status>
  </Cname>
  <Cname>
    <Domain>example.edu</Domain>
    <LastModified>2021-09-15T02:50:34.000Z</LastModified>
    <Status>Disabled</Status>
  </Cname>
</ListCnameResult>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().list_bucket_cname()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.bucket, 'targetbucket')
        self.assertEqual(result.owner, 'testowner')
        self.assertEqual(result.cname[0].domain, 'example.com')
        self.assertEqual(result.cname[0].last_modified, '2021-09-15T02:35:07.000Z')
        self.assertEqual(result.cname[0].status, 'Enabled')
        # self.assertEqual(result.cname[0].is_purge_cdn_cache, '2021-08-02T10:49:18.289372919+08:00')
        self.assertEqual(result.cname[0].certificate.type, 'CAS')
        self.assertEqual(result.cname[0].certificate.cert_id, '493****-cn-hangzhou')
        self.assertEqual(result.cname[0].certificate.status, 'Enabled')
        self.assertEqual(result.cname[0].certificate.creation_date, 'Wed, 15 Sep 2021 02:35:06 GMT')
        self.assertEqual(result.cname[0].certificate.fingerprint, 'DE:01:CF:EC:7C:A7:98:CB:D8:6E:FB:1D:97:EB:A9:64:1D:4E:**:**')
        self.assertEqual(result.cname[0].certificate.valid_start_date, 'Tues, 12 Apr 2021 10:14:51 GMT')
        self.assertEqual(result.cname[0].certificate.valid_end_date, 'Mon, 4 May 2048 10:14:51 GMT')
        self.assertEqual(result.cname[1].domain, 'example.org')
        self.assertEqual(result.cname[1].last_modified, '2021-09-15T02:34:58.000Z')
        self.assertEqual(result.cname[1].status, 'Enabled')
        self.assertEqual(result.cname[2].domain, 'example.edu')
        self.assertEqual(result.cname[2].last_modified, '2021-09-15T02:50:34.000Z')
        self.assertEqual(result.cname[2].status, 'Disabled')
        for c in result.cname:
            print(c.domain)
            print(c.last_modified)
            print(c.status)

    @patch('oss2.Session.do_request')
    def test_delete_bucket_cname(self, do_request):
        request_text = '''POST /?cname&comp=delete HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<BucketCnameConfiguration><Cname><Domain>{0}</Domain></Cname></BucketCnameConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
Date: Mon, 26 Jul 2021 13:08:38 GMT
Content-Length: 118
Content-Type: application/xml
Connection: keep-alive
Server: AliyunOSS
'''

        req_info = mock_response(do_request, response_text)
        domain = 'example.com'
        bucket().delete_bucket_cname(domain)
        self.assertRequest(req_info, request_text.format(to_string(domain)))

    @patch('oss2.Session.do_request')
    def test_open_bucket_meta_query(self, do_request):
        request_text = '''POST /?metaQuery HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****
'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length: 443
Connection: keep-alive
Server: AliyunOSS'''

        req_info = mock_response(do_request, response_text)

        result = bucket().open_bucket_meta_query()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)

    @patch('oss2.Session.do_request')
    def test_get_bucket_meta_query(self, do_request):
        request_text = '''GET /?metaQuery HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<MetaQuery>
  <State>Running</State>
  <Phase>FullScanning</Phase>
  <CreateTime>2021-08-02T10:49:17.289372919+08:00</CreateTime>
  <UpdateTime>2021-08-02T10:49:18.289372919+08:00</UpdateTime>
</MetaQuery>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_meta_query_status()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.state, 'Running')
        self.assertEqual(result.phase, 'FullScanning')
        self.assertEqual(result.create_time, '2021-08-02T10:49:17.289372919+08:00')
        self.assertEqual(result.update_time, '2021-08-02T10:49:18.289372919+08:00')

    @patch('oss2.Session.do_request')
    def test_do_bucket_meta_query(self, do_request):
        request_text = '''POST /?metaQuery&comp=query HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<?xml version="1.0" encoding="UTF-8"?>
<MetaQuery>
<NextToken>MTIzNDU2NzgnV9zYW1wbGVvYmplY3QxLmpwZw==</NextToken>
<MaxResults>120</MaxResults>
<Query>{"Field": "Size","Value": "1048576","Operation": "gt"}</Query>
<Sort>Size</Sort>
<Order>asc</Order>
<Aggregations>
<Aggregation>
<Field>Size</Field>
<Operation>sum</Operation>
</Aggregation>
<Aggregation>
<Field>Size</Field>
<Operation>max</Operation>
</Aggregation>
</Aggregations>
</MetaQuery>'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<MetaQuery>
    <NextToken>MTIzNDU2NzgnV9zYW1wbGVvYmplY3QxLmpwZw==</NextToken>
    <Files>    
        <File>     
            <Filename>exampleobject.txt</Filename>
            <Size>120</Size>
            <FileModifiedTime>2021-06-29T14:50:13.011643661+08:00</FileModifiedTime>
            <FileCreateTime>2021-06-28T14:50:13.011643661+08:00</FileCreateTime>
            <FileAccessTime>2021-06-27T14:50:13.011643661+08:00</FileAccessTime>
            <OSSObjectType>Normal</OSSObjectType>
            <OSSStorageClass>Standard</OSSStorageClass>
            <ObjectACL>defalut</ObjectACL>
            <ETag>fba9dede5f27731c9771645a3986****</ETag>
            <OSSCRC64>4858A48BD1466884</OSSCRC64>
            <OSSTaggingCount>2</OSSTaggingCount>
            <OSSTagging>
                <Tagging>
                    <Key>owner</Key>
                    <Value>John</Value>
                </Tagging>
                <Tagging>
                    <Key>type</Key>
                    <Value>document</Value>
                </Tagging>
            </OSSTagging>
            <OSSUserMeta>
                <UserMeta>
                    <Key>x-oss-meta-location</Key>
                    <Value>hangzhou</Value>
                </UserMeta>
            </OSSUserMeta>
        </File>
        <File>
          <Filename>file2</Filename>
          <Size>1</Size>
          <ObjectACL>private</ObjectACL>
          <OSSObjectType>Appendable</OSSObjectType>
          <OSSStorageClass>Standard</OSSStorageClass>
          <ETag>etag</ETag>
          <OSSCRC64>crc</OSSCRC64>
          <OSSTaggingCount>2</OSSTaggingCount>
          <OSSTagging>
            <Tagging>
              <Key>t3</Key>
              <Value>v3</Value>
            </Tagging>
            <Tagging>
              <Key>t4</Key>
              <Value>v4</Value>
            </Tagging>
          </OSSTagging>
          <OSSUserMeta>
            <UserMeta>
              <Key>u3</Key>
              <Value>v3</Value>
            </UserMeta>
            <UserMeta>
              <Key>u4</Key>
              <Value>v4</Value>
            </UserMeta>
          </OSSUserMeta>
        </File>
    </Files>
    <Aggregations>
            <Aggregation>
              <Field>Size</Field>
              <Operation>sum</Operation>
              <Value>200</Value>
              <Groups>
                <Group>
                    <Value>100</Value>
                    <Count>5</Count>
                </Group>
                <Group>
                    <Value>300</Value>
                    <Count>6</Count>
                </Group>
              </Groups>
            </Aggregation>
            <Aggregation>
              <Field>Size</Field>
              <Operation>max</Operation>
              <Value>200.2</Value>
            </Aggregation>
            <Aggregation>
              <Field>field1</Field>
              <Operation>operation1</Operation>
              <Groups>
                <Group>
                  <Value>value1</Value>
                  <Count>10</Count>
                </Group>
                <Group>
                  <Value>value2</Value>
                  <Count>20</Count>
                </Group>
              </Groups>
            </Aggregation>
        </Aggregations>
</MetaQuery>'''

        req_info = mock_response(do_request, response_text)
        aggregation1 = AggregationsRequest('Size', 'sum')
        aggregation2 = AggregationsRequest('Size', 'max')
        do_meta_query_request = MetaQuery('MTIzNDU2NzgnV9zYW1wbGVvYmplY3QxLmpwZw==', 120, '{"Field": "Size","Value": "1048576","Operation": "gt"}', 'Size', 'asc', [aggregation1, aggregation2])
        result = bucket().do_bucket_meta_query(do_meta_query_request)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.next_token, 'MTIzNDU2NzgnV9zYW1wbGVvYmplY3QxLmpwZw==')
        self.assertEqual(result.files[0].file_name, 'exampleobject.txt')
        self.assertEqual(result.files[0].size, 120)
        self.assertEqual(result.files[0].file_modified_time, '2021-06-29T14:50:13.011643661+08:00')
        self.assertEqual(result.files[0].file_create_time, '2021-06-28T14:50:13.011643661+08:00')
        self.assertEqual(result.files[0].file_access_time, '2021-06-27T14:50:13.011643661+08:00')
        self.assertEqual(result.files[0].oss_object_type, 'Normal')
        self.assertEqual(result.files[0].oss_storage_class, 'Standard')
        self.assertEqual(result.files[0].object_acl, 'defalut')
        self.assertEqual(result.files[0].etag, 'fba9dede5f27731c9771645a3986****')
        self.assertEqual(result.files[0].oss_crc64, '4858A48BD1466884')
        self.assertEqual(result.files[0].oss_tagging_count, 2)
        self.assertEqual(result.files[0].oss_tagging[0].key, 'owner')
        self.assertEqual(result.files[0].oss_tagging[0].value, 'John')
        self.assertEqual(result.files[0].oss_tagging[1].key, 'type')
        self.assertEqual(result.files[0].oss_tagging[1].value, 'document')
        self.assertEqual(result.files[0].oss_user_meta[0].key, 'x-oss-meta-location')
        self.assertEqual(result.files[0].oss_user_meta[0].value, 'hangzhou')
        self.assertEqual(result.files[1].file_name, 'file2')
        self.assertEqual(result.files[1].size, 1)
        self.assertEqual(result.files[1].oss_object_type, 'Appendable')
        self.assertEqual(result.files[1].oss_storage_class, 'Standard')
        self.assertEqual(result.files[1].object_acl, 'private')
        self.assertEqual(result.files[1].etag, 'etag')
        self.assertEqual(result.files[1].oss_crc64, 'crc')
        self.assertEqual(result.files[1].oss_tagging_count, 2)
        self.assertEqual(result.files[1].oss_tagging[0].key, 't3')
        self.assertEqual(result.files[1].oss_tagging[0].value, 'v3')
        self.assertEqual(result.files[1].oss_tagging[1].key, 't4')
        self.assertEqual(result.files[1].oss_tagging[1].value, 'v4')
        self.assertEqual(result.files[1].oss_user_meta[0].key, 'u3')
        self.assertEqual(result.files[1].oss_user_meta[0].value, 'v3')
        self.assertEqual(result.files[1].oss_user_meta[1].key, 'u4')
        self.assertEqual(result.files[1].oss_user_meta[1].value, 'v4')
        self.assertEqual(result.aggregations[0].field, 'Size')
        self.assertEqual(result.aggregations[0].operation, 'sum')
        self.assertEqual(result.aggregations[0].value, 200)
        self.assertEqual(result.aggregations[0].groups[0].value, '100')
        self.assertEqual(result.aggregations[0].groups[0].count, 5)
        self.assertEqual(result.aggregations[0].groups[1].value, '300')
        self.assertEqual(result.aggregations[0].groups[1].count, 6)
        self.assertEqual(result.aggregations[1].field, 'Size')
        self.assertEqual(result.aggregations[1].operation, 'max')
        self.assertEqual(result.aggregations[1].value, 200.2)
        self.assertEqual(result.aggregations[2].field, 'field1')
        self.assertEqual(result.aggregations[2].operation, 'operation1')
        self.assertEqual(result.aggregations[2].groups[0].value, 'value1')
        self.assertEqual(result.aggregations[2].groups[0].count, 10)
        self.assertEqual(result.aggregations[2].groups[1].value, 'value2')
        self.assertEqual(result.aggregations[2].groups[1].count, 20)

    @patch('oss2.Session.do_request')
    def test_close_bucket_meta_query(self, do_request):
        request_text = '''POST /?metaQuery&comp=delete HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT
'''

        req_info = mock_response(do_request, response_text)

        result = bucket().close_bucket_meta_query()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)

if __name__ == '__main__':
    unittest.main()
