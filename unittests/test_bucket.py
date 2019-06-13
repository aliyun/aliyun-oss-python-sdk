# -*- coding: utf-8 -*-

import datetime

from mock import patch
from functools import partial

from oss2 import to_string
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


if __name__ == '__main__':
    unittest.main()
