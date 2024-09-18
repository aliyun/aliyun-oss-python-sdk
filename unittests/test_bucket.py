# -*- coding: utf-8 -*-

import datetime

from mock import patch
from functools import partial

from oss2 import to_string, iso8601_to_unixtime
from oss2.headers import OSS_ALLOW_ACTION_OVERLAP
from oss2.models import AggregationsRequest, MetaQuery, CallbackPolicyInfo, BucketTlsVersion, \
    AccessPointVpcConfiguration, CreateAccessPointRequest, QoSConfiguration
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
    def test_put_lifecycle_overlap(self, do_request):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        request_text = '''PUT /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 198
x-oss-allow-same-action-overlap: true
date: Sat, 12 Dec 2015 00:35:37 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:45HTpSD5osRvtusf8VCkmchZZFs=

<LifecycleConfiguration><Rule><ID>{0}</ID><Prefix>{1}</Prefix><Status>{2}</Status><Expiration><Date>{3}</Date></Expiration></Rule><Rule><ID>{4}</ID><Prefix>{5}</Prefix><Status>{6}</Status><Expiration><Date>{7}</Date></Expiration></Rule></LifecycleConfiguration>'''

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
        id_global = 'hello global'
        prefix_global = '中文-同样前缀'
        status_global = 'Disabled'
        date_global = '2015-12-25T00:00:00.000Z'

        headers = dict()
        headers[OSS_ALLOW_ACTION_OVERLAP] = 'true'
        req_info = mock_response(do_request, response_text)
        rule = LifecycleRule(id, prefix,
                             status=LifecycleRule.DISABLED,
                             expiration=LifecycleExpiration(date=datetime.date(2015, 12, 25)))
        rule_global = LifecycleRule(id_global, prefix_global,
                                    status=LifecycleRule.DISABLED,
                                    expiration=LifecycleExpiration(date=datetime.date(2015, 12, 25)))
        lifecycle = BucketLifecycle([rule])
        lifecycle.rules.append(rule_global)
        bucket().put_bucket_lifecycle(lifecycle, headers)

        self.assertRequest(req_info, request_text.format(id, prefix, status, date, id_global, prefix_global, status_global, date_global))

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
    def test_put_cors_with_response_vary(self, do_request):
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

<CORSConfiguration><CORSRule><AllowedOrigin>*</AllowedOrigin><AllowedMethod>HEAD</AllowedMethod><AllowedMethod>GET</AllowedMethod><AllowedHeader>*</AllowedHeader><MaxAgeSeconds>1000</MaxAgeSeconds></CORSRule><ResponseVary>true</ResponseVary></CORSConfiguration>'''

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

        bucket().put_bucket_cors(oss2.models.BucketCors([rule], response_vary=True))

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
    def test_get_cors_with_response_vary(self, do_request):
        request_text = '''GET /?cors= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:37 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:wfV1/6+sVdNzsXbHEXZQeQRC7xk='''

        response_text_true = '''HTTP/1.1 200 OK
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
    <ResponseVary>true</ResponseVary>
</CORSConfiguration>'''

        response_text_false = '''HTTP/1.1 200 OK
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
    <ResponseVary>false</ResponseVary>
</CORSConfiguration>'''

        #ResponseVary  is true
        req_info = mock_response(do_request, response_text_true)

        result = bucket().get_bucket_cors()

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.rules[0].allowed_origins, ['*'])
        self.assertEqual(result.rules[0].allowed_methods, ['PUT', 'GET'])
        self.assertEqual(result.rules[0].allowed_headers, ['Authorization'])

        self.assertEqual(result.rules[1].allowed_origins, ['http://www.a.com', 'www.b.com'])
        self.assertEqual(result.rules[1].allowed_methods, ['GET'])
        self.assertEqual(result.rules[1].expose_headers, ['x-oss-test', 'x-oss-test1'])
        self.assertEqual(result.rules[1].max_age_seconds, 100)
        self.assertEqual(result.response_vary, True)

        #ResponseVary  is False
        req_info = mock_response(do_request, response_text_false)

        result = bucket().get_bucket_cors()

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.rules[0].allowed_origins, ['*'])
        self.assertEqual(result.rules[0].allowed_methods, ['PUT', 'GET'])
        self.assertEqual(result.rules[0].allowed_headers, ['Authorization'])

        self.assertEqual(result.rules[1].allowed_origins, ['http://www.a.com', 'www.b.com'])
        self.assertEqual(result.rules[1].allowed_methods, ['GET'])
        self.assertEqual(result.rules[1].expose_headers, ['x-oss-test', 'x-oss-test1'])
        self.assertEqual(result.rules[1].max_age_seconds, 100)
        self.assertEqual(result.response_vary, False)


    @patch('oss2.Session.do_request')
    def test_get_cors_with_response_vary_2(self, do_request):
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
    </CORSRule>
</CORSConfiguration>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_cors()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.response_vary, None)


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
    def test_get_stat_part_param(self, do_request):
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
        self.assertEqual(result.live_channel_count, None)
        self.assertEqual(result.last_modified_time, None)
        self.assertEqual(result.standard_storage, None)
        self.assertEqual(result.standard_object_count, None)
        self.assertEqual(result.infrequent_access_storage, None)
        self.assertEqual(result.infrequent_access_real_storage, None)
        self.assertEqual(result.infrequent_access_object_count, None)
        self.assertEqual(result.archive_storage, None)
        self.assertEqual(result.archive_real_storage, None)
        self.assertEqual(result.archive_object_count, None)
        self.assertEqual(result.cold_archive_storage, None)
        self.assertEqual(result.cold_archive_real_storage, None)
        self.assertEqual(result.cold_archive_object_count, None)
        self.assertEqual(result.multipart_part_count, None)
        self.assertEqual(result.delete_marker_count, None)


    @patch('oss2.Session.do_request')
    def test_get_stat_multipart_part_count(self, do_request):
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
    <ColdArchiveRealStorage>360</ColdArchiveRealStorage>
    <ColdArchiveObjectCount>36</ColdArchiveObjectCount>
    <MultipartPartCount>4</MultipartPartCount>
    <DeleteMarkerCount>164</DeleteMarkerCount>
</BucketStat>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_stat()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.storage_size_in_bytes, 472594058)
        self.assertEqual(result.object_count, 666)
        self.assertEqual(result.multi_part_upload_count, 992)
        self.assertEqual(result.multipart_part_count, 4)
        self.assertEqual(result.delete_marker_count, 164)


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

    @patch('oss2.Session.do_request')
    def test_put_bucket_inventory(self, do_request):
        request_text = '''PUT /?inventory&inventoryId=report1 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<?xml version="1.0" encoding="UTF-8"?>
<InventoryConfiguration>
<Id>{0}</Id>
<IsEnabled>True</IsEnabled>
<IncludedObjectVersions>All</IncludedObjectVersions>
<Filter>
<Prefix>Pics/</Prefix>
<LastModifyBeginTimeStamp>1637883649</LastModifyBeginTimeStamp>
<LastModifyEndTimeStamp>1638347592</LastModifyEndTimeStamp>
<LowerSizeBound>1024</LowerSizeBound>
<UpperSizeBound>1048576</UpperSizeBound>
<StorageClass>Standard,IA</StorageClass>
</Filter>
<Schedule>
<Frequency>Daily</Frequency>
</Schedule>
<OptionalFields>
<Field>Size</Field>
<Field>LastModifiedDate</Field>
<Field>StorageClass</Field>
<Field>ETag</Field>
<Field>IsMultipartUploaded</Field>
<Field>EncryptionStatus</Field>
</OptionalFields>
<Destination>
<OSSBucketDestination>
<AccountId>100000000000000</AccountId>
<RoleArn>acs:ram::100000000000000:role/AliyunOSSRole</RoleArn>
<Bucket>acs:oss:::acs:oss:::bucket_0001</Bucket>
<Format>CSV</Format>
<Prefix>prefix1</Prefix>
<Encryption>
<SSE-OSS/>
</Encryption>
</OSSBucketDestination>
</Destination>
</InventoryConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)
        optional_fields = [oss2.models.FIELD_SIZE, oss2.models.FIELD_LAST_MODIFIED_DATE, oss2.models.FIELD_STORAG_CLASS,
                           oss2.models.FIELD_ETAG, oss2.models.FIELD_IS_MULTIPART_UPLOADED, oss2.models.FIELD_ENCRYPTION_STATUS]
        bucket_destination = oss2.models.InventoryBucketDestination(
            account_id='100000000000000',
            role_arn='acs:ram::100000000000000:role/AliyunOSSRole',
            bucket='acs:oss:::bucket_0001',
            inventory_format='CSV',
            prefix="prefix1",
            sse_oss_encryption=oss2.models.InventoryServerSideEncryptionOSS())

        inventory_configuration = oss2.models.InventoryConfiguration(
            inventory_id='report1',
            is_enabled=True,
            inventory_schedule=oss2.models.InventorySchedule(frequency='Daily'),
            included_object_versions='All',
            inventory_filter=oss2.models.InventoryFilter(prefix="Pics/", last_modify_begin_time_stamp=1637883649, last_modify_end_time_stamp=1638347592, lower_size_bound=1024,
                                                         upper_size_bound=1048576, storage_class='Standard,IA'),
            optional_fields=optional_fields,
            inventory_destination=oss2.models.InventoryDestination(bucket_destination=bucket_destination))

        bucket().put_bucket_inventory_configuration(inventory_configuration)
        self.assertRequest(req_info, request_text.format(to_string('report1')))


    @patch('oss2.Session.do_request')
    def test_get_bucket_inventory(self, do_request):
        request_text = '''GET /?inventory&inventoryId=list1 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<InventoryConfiguration>
    <Id>list1</Id>
    <IsEnabled>false</IsEnabled>
    <IncludedObjectVersions>All</IncludedObjectVersions>
    <Filter>
        <Prefix>testPrefix</Prefix>
        <LastModifyBeginTimeStamp></LastModifyBeginTimeStamp>
        <LastModifyEndTimeStamp>1638347592</LastModifyEndTimeStamp>
        <LowerSizeBound>1024</LowerSizeBound>
        <UpperSizeBound>1048576</UpperSizeBound>
        <StorageClass>Standard,IA</StorageClass>
    </Filter>
    <Schedule>
        <Frequency>Weekly</Frequency>
    </Schedule>
    <OptionalFields>
        <Field>Size</Field>
        <Field>LastModifiedDate</Field>
        <Field>ETag</Field>
        <Field>StorageClass</Field>
        <Field>IsMultipartUploaded</Field>
        <Field>EncryptionStatus</Field>
    </OptionalFields>
    <Destination>
        <OSSBucketDestination>
            <AccountId>1283641064516515</AccountId>
            <RoleArn>acs:ram::1283641064516515:role/AliyunOSSRole</RoleArn>
            <Bucket>acs:oss:::oss-java-sdk-1655373445-inventory-destin</Bucket>
            <Prefix>bucket-prefix</Prefix>
            <Format>CSV</Format>
            <Encryption>
                <SSE-OSS></SSE-OSS>
            </Encryption>
        </OSSBucketDestination>
    </Destination>
</InventoryConfiguration>'''

        req_info = mock_response(do_request, response_text)
        inventory_id = 'list1'
        result = bucket().get_bucket_inventory_configuration(inventory_id)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.inventory_filter.prefix, 'testPrefix')
        self.assertEqual(result.inventory_filter.last_modify_begin_time_stamp, '')
        self.assertEqual(int(result.inventory_filter.last_modify_end_time_stamp), 1638347592)
        self.assertEqual(int(result.inventory_filter.lower_size_bound), 1024)
        self.assertEqual(int(result.inventory_filter.upper_size_bound), 1048576)
        self.assertEqual(result.inventory_filter.storage_class, 'Standard,IA')


    @patch('oss2.Session.do_request')
    def test_list_bucket_inventory(self, do_request):
        request_text = '''GET /?inventory&continuation-token=aa HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<ListInventoryConfigurationsResult>
     <InventoryConfiguration>
        <Id>report1</Id>
        <IsEnabled>true</IsEnabled>
        <Destination>
           <OSSBucketDestination>
              <Format>CSV</Format>
              <AccountId>1000000000000000</AccountId>
              <RoleArn>acs:ram::1000000000000000:role/AliyunOSSRole</RoleArn>
              <Bucket>acs:oss:::destination-bucket</Bucket>
              <Prefix>prefix1</Prefix>
           </OSSBucketDestination>
        </Destination>
        <Schedule>
           <Frequency>Daily</Frequency>
        </Schedule>
        <Filter>
           <Prefix>prefix/One</Prefix>
           <LastModifyBeginTimeStamp></LastModifyBeginTimeStamp>
            <LastModifyEndTimeStamp>1638347592</LastModifyEndTimeStamp>
            <LowerSizeBound>1024</LowerSizeBound>
            <UpperSizeBound>1048576</UpperSizeBound>
            <StorageClass>Standard,IA</StorageClass>
        </Filter>
        <IncludedObjectVersions>All</IncludedObjectVersions>
        <OptionalFields>
           <Field>Size</Field>
           <Field>LastModifiedDate</Field>
           <Field>ETag</Field>
           <Field>StorageClass</Field>
           <Field>IsMultipartUploaded</Field>
           <Field>EncryptionStatus</Field>
        </OptionalFields>
     </InventoryConfiguration>
     <InventoryConfiguration>
        <Id>report2</Id>
        <IsEnabled>true</IsEnabled>
        <Destination>
           <OSSBucketDestination>
              <Format>CSV</Format>
              <AccountId>1000000000000000</AccountId>
              <RoleArn>acs:ram::1000000000000000:role/AliyunOSSRole</RoleArn>
              <Bucket>acs:oss:::destination-bucket</Bucket>
              <Prefix>prefix2</Prefix>
           </OSSBucketDestination>
        </Destination>
        <Schedule>
           <Frequency>Daily</Frequency>
        </Schedule>
        <Filter>
           <Prefix>prefix/Two</Prefix>
        </Filter>
        <IncludedObjectVersions>All</IncludedObjectVersions>
        <OptionalFields>
           <Field>Size</Field>
           <Field>LastModifiedDate</Field>
           <Field>ETag</Field>
           <Field>StorageClass</Field>
           <Field>IsMultipartUploaded</Field>
           <Field>EncryptionStatus</Field>
        </OptionalFields>
     </InventoryConfiguration>
     <InventoryConfiguration>
        <Id>report3</Id>
        <IsEnabled>true</IsEnabled>
        <Destination>
           <OSSBucketDestination>
              <Format>CSV</Format>
              <AccountId>1000000000000000</AccountId>
              <RoleArn>acs:ram::1000000000000000:role/AliyunOSSRole</RoleArn>
              <Bucket>acs:oss:::destination-bucket</Bucket>
              <Prefix>prefix3</Prefix>
           </OSSBucketDestination>
        </Destination>
        <Schedule>
           <Frequency>Daily</Frequency>
        </Schedule>
        <Filter>
           <Prefix>prefix/Three</Prefix>
            <LowerSizeBound>111</LowerSizeBound>
            <StorageClass>Standard</StorageClass>
        </Filter>
        <IncludedObjectVersions>All</IncludedObjectVersions>
        <OptionalFields>
           <Field>Size</Field>
           <Field>LastModifiedDate</Field>
           <Field>ETag</Field>
           <Field>StorageClass</Field>
           <Field>IsMultipartUploaded</Field>
           <Field>EncryptionStatus</Field>
        </OptionalFields>
     </InventoryConfiguration>
     <IsTruncated>true</IsTruncated>
     <NextContinuationToken>aa</NextContinuationToken> 
  </ListInventoryConfigurationsResult>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().list_bucket_inventory_configurations('aa')

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.inventory_configurations[0].inventory_filter.prefix, 'prefix/One')
        self.assertEqual(result.inventory_configurations[0].inventory_filter.last_modify_begin_time_stamp, '')
        self.assertEqual(int(result.inventory_configurations[0].inventory_filter.last_modify_end_time_stamp), 1638347592)
        self.assertEqual(int(result.inventory_configurations[0].inventory_filter.lower_size_bound), 1024)
        self.assertEqual(int(result.inventory_configurations[0].inventory_filter.upper_size_bound), 1048576)
        self.assertEqual(result.inventory_configurations[0].inventory_filter.storage_class, 'Standard,IA')
        self.assertEqual(result.inventory_configurations[2].inventory_filter.prefix, 'prefix/Three')
        self.assertEqual(int(result.inventory_configurations[2].inventory_filter.lower_size_bound), 111)
        self.assertEqual(result.inventory_configurations[2].inventory_filter.storage_class, 'Standard')

    @patch('oss2.Session.do_request')
    def test_delete_inventory(self, do_request):
        request_text = '''DELETE ?/inventory&inventoryId=list1 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT
'''

        req_info = mock_response(do_request, response_text)
        inventory_id = 'test-id'
        result = bucket().delete_bucket_inventory_configuration(inventory_id)

        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)

    @patch('oss2.Session.do_request')
    def test_put_bucket_access_monitor(self, do_request):
        request_text = '''PUT /?accessmonitor HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<AccessMonitorConfiguration><Status>Enabled</Status></AccessMonitorConfiguration>
'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)

        result = bucket().put_bucket_access_monitor('Enabled')

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '5C1B138A109F4E405B2D')
        self.assertEqual(result.status, 200)


    @patch('oss2.Session.do_request')
    def test_get_bucket_access_monitor(self, do_request):
        request_text = '''GET /?accessmonitor HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<AccessMonitorConfiguration>
  <Status>Enabled</Status>
</AccessMonitorConfiguration>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_access_monitor()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.access_monitor.status, 'Enabled')


    @patch('oss2.Session.do_request')
    def test_put_lifecycle_access_monitor(self, do_request):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition

        request_text = '''PUT /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 198
date: Sat, 12 Dec 2015 00:35:37 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:45HTpSD5osRvtusf8VCkmchZZFs=

<LifecycleConfiguration>
<Rule>
<ID>{0}</ID>
<Prefix>{1}</Prefix>
<Status>{2}</Status>
<Expiration>
<Date>{3}</Date>
</Expiration>
<Transition>
<StorageClass>{5}</StorageClass>
<IsAccessTime>{6}</IsAccessTime>
<ReturnToStdWhenVisit>{7}</ReturnToStdWhenVisit>
<AllowSmallFile>{8}</AllowSmallFile>
<Days>{4}</Days>
</Transition>
</Rule>
</LifecycleConfiguration>'''

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
        days = 30
        storage_class = 'IA'
        is_access_time = True
        return_to_std_when_visit = True
        allow_small_file = True

        req_info = mock_response(do_request, response_text)
        rule = LifecycleRule(id, prefix,
                             status=LifecycleRule.DISABLED,
                             expiration=LifecycleExpiration(date=datetime.date(2015, 12, 25)))
        rule.storage_transitions = [StorageTransition(days=30,
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA, is_access_time=True, return_to_std_when_visit=True, allow_small_file=True)]
        bucket().put_bucket_lifecycle(BucketLifecycle([rule]))

        self.assertRequest(req_info, request_text.format(id, prefix, status, date, days, storage_class, str(is_access_time).lower(), str(return_to_std_when_visit).lower(), str(allow_small_file).lower()))


    @patch('oss2.Session.do_request')
    def test_get_lifecycle_access_monitor(self, do_request):
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
    <NoncurrentVersionTransition>
      <NoncurrentDays>{4}</NoncurrentDays>
      <StorageClass>{5}</StorageClass>
      <IsAccessTime>{6}</IsAccessTime>
      <ReturnToStdWhenVisit>{7}</ReturnToStdWhenVisit>
      <AllowSmallFile>{8}</AllowSmallFile>
    </NoncurrentVersionTransition>
  </Rule>
</LifecycleConfiguration>'''

        id = 'whatever'
        prefix = 'lifecycle rule 1'
        status = LifecycleRule.DISABLED
        date = datetime.date(2015, 12, 25)
        days = 30
        storage_class = 'IA'
        is_access_time = True
        return_to_std_when_visit = False
        allow_small_file = True

        req_info = mock_response(do_request, response_text.format(id, prefix, status, '2015-12-25T00:00:00.000Z',
                                 days, storage_class, str(is_access_time).lower(), str(return_to_std_when_visit).lower(), str(allow_small_file).lower()))
        result = bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, date)
        self.assertEqual(rule.noncurrent_version_sotrage_transitions[0].noncurrent_days, days)
        self.assertEqual(rule.noncurrent_version_sotrage_transitions[0].storage_class, storage_class)
        self.assertEqual(rule.noncurrent_version_sotrage_transitions[0].is_access_time, is_access_time)
        self.assertEqual(rule.noncurrent_version_sotrage_transitions[0].return_to_std_when_visit, return_to_std_when_visit)
        self.assertEqual(rule.noncurrent_version_sotrage_transitions[0].allow_small_file, allow_small_file)


    @patch('oss2.Session.do_request')
    def test_put_lifecycle_not(self, do_request):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, LifecycleFilter, FilterNot, FilterNotTag

        request_text = '''PUT /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 198
date: Sat, 12 Dec 2015 00:35:37 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:45HTpSD5osRvtusf8VCkmchZZFs=

<LifecycleConfiguration>
<Rule>
<ID>{0}</ID>
<Prefix>{1}</Prefix>
<Status>{2}</Status>
<Expiration>
<Date>{3}</Date>
</Expiration>
<Filter>
<Not>
<Prefix>{4}</Prefix>
<Tag>
<Key>{5}</Key>
<Value>{6}</Value>
</Tag>
</Not>
</Filter>
</Rule>
</LifecycleConfiguration>'''

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
        not_prefix = 'not'
        key = 'key'
        value = 'value'
        not_tag = FilterNotTag(key, value)
        filter_not = FilterNot(not_prefix, not_tag)
        filter = LifecycleFilter([filter_not])

        req_info = mock_response(do_request, response_text)
        rule = LifecycleRule(id, prefix,
                             status=LifecycleRule.DISABLED,
                             expiration=LifecycleExpiration(date=datetime.date(2015, 12, 25)),
                             filter=filter)
        bucket().put_bucket_lifecycle(BucketLifecycle([rule]))

        self.assertRequest(req_info, request_text.format(id, prefix, status, date, not_prefix, key, value))


    @patch('oss2.Session.do_request')
    def test_put_lifecycle_filter_object_size_than(self, do_request):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, LifecycleFilter, FilterNot, FilterNotTag

        request_text = '''PUT /?lifecycle= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 198
date: Sat, 12 Dec 2015 00:35:37 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:45HTpSD5osRvtusf8VCkmchZZFs=

<LifecycleConfiguration>
<Rule>
<ID>{0}</ID>
<Prefix>{1}</Prefix>
<Status>{2}</Status>
<Expiration>
<Date>{3}</Date>
</Expiration>
<Filter>
<ObjectSizeGreaterThan>{4}</ObjectSizeGreaterThan>
<ObjectSizeLessThan>{5}</ObjectSizeLessThan>
<Not>
<Prefix>{6}</Prefix>
<Tag>
<Key>{7}</Key>
<Value>{8}</Value>
</Tag>
</Not>
</Filter>
</Rule>
</LifecycleConfiguration>'''

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
        not_prefix = 'not'
        key = 'key'
        value = 'value'
        object_size_greater_than = 500
        object_size_less_than = 64000
        not_tag = FilterNotTag(key, value)
        filter_not = FilterNot(not_prefix, not_tag)
        filter = LifecycleFilter([filter_not],object_size_greater_than,object_size_less_than)

        req_info = mock_response(do_request, response_text)
        rule = LifecycleRule(id, prefix,
                             status=LifecycleRule.DISABLED,
                             expiration=LifecycleExpiration(date=datetime.date(2015, 12, 25)),
                             filter=filter)
        bucket().put_bucket_lifecycle(BucketLifecycle([rule]))

        self.assertRequest(req_info, request_text.format(id, prefix, status, date, object_size_greater_than, object_size_less_than, not_prefix, key, value))


    @patch('oss2.Session.do_request')
    def test_get_lifecycle_not(self, do_request):
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
    <Filter>
        <Not>
            <Prefix>{4}</Prefix>
            <Tag>
                <Key>{5}</Key>
                <Value>{6}</Value>
            </Tag>
        </Not>
    </Filter>
  </Rule>
</LifecycleConfiguration>'''

        id = 'whatever'
        prefix = 'lifecycle rule 1'
        status = LifecycleRule.DISABLED
        date = datetime.date(2015, 12, 25)
        not_prefix = 'not'
        key = 'key'
        value = 'value'

        req_info = mock_response(do_request, response_text.format(id, prefix, status, '2015-12-25T00:00:00.000Z', not_prefix, key, value))
        result = bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, date)
        self.assertEqual(rule.expiration.days, None)
        self.assertEqual(rule.filter.filter_not[0].prefix, not_prefix)
        self.assertEqual(rule.filter.filter_not[0].tag.key, key)
        self.assertEqual(rule.filter.filter_not[0].tag.value, value)


    @patch('oss2.Session.do_request')
    def test_get_lifecycle_nots(self, do_request):
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
    <Filter>
        <Not>
            <Prefix>{4}</Prefix>
            <Tag>
                <Key>{5}</Key>
                <Value>{6}</Value>
            </Tag>
        </Not>
        <Not>
            <Prefix>{7}</Prefix>
        </Not>
    </Filter>
  </Rule>
</LifecycleConfiguration>'''

        id = 'whatever'
        prefix = 'lifecycle rule 1'
        status = LifecycleRule.DISABLED
        date = datetime.date(2015, 12, 25)
        not_prefix = 'not'
        key = 'key'
        value = 'value'
        not_prefix2 = 'not2'

        req_info = mock_response(do_request, response_text.format(id, prefix, status, '2015-12-25T00:00:00.000Z', not_prefix, key, value, not_prefix2))
        result = bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, date)
        self.assertEqual(rule.expiration.days, None)
        self.assertEqual(rule.filter.filter_not[0].prefix, not_prefix)
        self.assertEqual(rule.filter.filter_not[0].tag.key, key)
        self.assertEqual(rule.filter.filter_not[0].tag.value, value)
        self.assertEqual(rule.filter.filter_not[1].prefix, not_prefix2)


    @patch('oss2.Session.do_request')
    def test_get_lifecycle_object_size_than(self, do_request):
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
    <Filter>
        <ObjectSizeGreaterThan>500</ObjectSizeGreaterThan>
        <ObjectSizeLessThan>64000</ObjectSizeLessThan>
        <Not>
            <Prefix>{4}</Prefix>
            <Tag>
                <Key>{5}</Key>
                <Value>{6}</Value>
            </Tag>
        </Not>
        <Not>
            <Prefix>{7}</Prefix>
        </Not>
    </Filter>
  </Rule>
</LifecycleConfiguration>'''

        id = 'whatever'
        prefix = 'lifecycle rule 1'
        status = LifecycleRule.DISABLED
        date = datetime.date(2015, 12, 25)
        not_prefix = 'not'
        key = 'key'
        value = 'value'
        not_prefix2 = 'not2'

        req_info = mock_response(do_request, response_text.format(id, prefix, status, '2015-12-25T00:00:00.000Z', not_prefix, key, value, not_prefix2))
        result = bucket().get_bucket_lifecycle()

        self.assertRequest(req_info, request_text)

        rule = result.rules[0]
        self.assertEqual(rule.id, id)
        self.assertEqual(rule.prefix, prefix)
        self.assertEqual(rule.status, status)
        self.assertEqual(rule.expiration.date, date)
        self.assertEqual(rule.expiration.days, None)
        self.assertEqual(rule.filter.object_size_greater_than, 500)
        self.assertEqual(rule.filter.object_size_less_than, 64000)
        self.assertEqual(rule.filter.filter_not[0].prefix, not_prefix)
        self.assertEqual(rule.filter.filter_not[0].tag.key, key)
        self.assertEqual(rule.filter.filter_not[0].tag.value, value)
        self.assertEqual(rule.filter.filter_not[1].prefix, not_prefix2)


    @patch('oss2.Session.do_request')
    def test_put_bucket_resource_group(self, do_request):
        request_text = '''PUT /?resourceGroup HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<BucketResourceGroupConfiguration>
<ResourceGroupId>{0}</ResourceGroupId>
</BucketResourceGroupConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)
        resourceGroupId = 'rg-xxxxxx'
        bucket().put_bucket_resource_group(resourceGroupId)
        self.assertRequest(req_info, request_text.format(to_string(resourceGroupId)))

    @patch('oss2.Session.do_request')
    def test_get_bucket_resource_group(self, do_request):
        request_text = '''GET /?resourceGroup HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<BucketResourceGroupConfiguration>
  <ResourceGroupId>rg-xxxxxx</ResourceGroupId>
</BucketResourceGroupConfiguration>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_resource_group()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.resource_group_id, 'rg-xxxxxx')

    @patch('oss2.Session.do_request')
    def test_put_bucket_style(self, do_request):
        request_text = '''PUT /?style&styleName=imagestyle HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<Style>
<Content>{0}</Content>
</Style>'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)
        content = 'image/resize,p_50'
        bucket().put_bucket_style('imagestyle',content)
        self.assertRequest(req_info, request_text.format(to_string(content)))

    @patch('oss2.Session.do_request')
    def test_get_bucket_style(self, do_request):
        request_text = '''GET /?style&styleName=imagestyle HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<Style>
 <Name>imagestyle</Name>
 <Content>image/resize,p_50</Content>
 <CreateTime>Wed, 20 May 2020 12:07:15 GMT</CreateTime>
 <LastModifyTime>Wed, 21 May 2020 12:07:15 GMT</LastModifyTime>
</Style>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_style('imagestyle')

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.name, 'imagestyle')
        self.assertEqual(result.content, 'image/resize,p_50')
        self.assertEqual(result.create_time, 'Wed, 20 May 2020 12:07:15 GMT')
        self.assertEqual(result.last_modify_time, 'Wed, 21 May 2020 12:07:15 GMT')


    @patch('oss2.Session.do_request')
    def test_list_bucket_style(self, do_request):
        request_text = '''GET /?style HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<StyleList>
 <Style>
 <Name>imagestyle</Name>
 <Content>image/resize,p_50</Content>
 <CreateTime>Wed, 20 May 2020 12:07:15 GMT</CreateTime>
 <LastModifyTime>Wed, 21 May 2020 12:07:15 GMT</LastModifyTime>
 </Style>
 <Style>
 <Name>imagestyle1</Name>
 <Content>image/resize,w_200</Content>
 <CreateTime>Wed, 20 May 2020 12:08:04 GMT</CreateTime>
 <LastModifyTime>Wed, 21 May 2020 12:08:04 GMT</LastModifyTime>
 </Style>
 <Style>
 <Name>imagestyle2</Name>
 <Content>image/resize,w_300</Content>
 <CreateTime>Fri, 12 Mar 2021 06:19:13 GMT</CreateTime>
 <LastModifyTime>Fri, 13 Mar 2021 06:27:21 GMT</LastModifyTime>
 </Style>
</StyleList>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().list_bucket_style()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.styles[0].name, 'imagestyle')
        self.assertEqual(result.styles[0].content, 'image/resize,p_50')
        self.assertEqual(result.styles[0].create_time, 'Wed, 20 May 2020 12:07:15 GMT')
        self.assertEqual(result.styles[0].last_modify_time, 'Wed, 21 May 2020 12:07:15 GMT')
        self.assertEqual(result.styles[1].name, 'imagestyle1')
        self.assertEqual(result.styles[1].content, 'image/resize,w_200')
        self.assertEqual(result.styles[1].create_time, 'Wed, 20 May 2020 12:08:04 GMT')
        self.assertEqual(result.styles[1].last_modify_time, 'Wed, 21 May 2020 12:08:04 GMT')
        self.assertEqual(result.styles[2].name, 'imagestyle2')
        self.assertEqual(result.styles[2].content, 'image/resize,w_300')
        self.assertEqual(result.styles[2].create_time, 'Fri, 12 Mar 2021 06:19:13 GMT')
        self.assertEqual(result.styles[2].last_modify_time, 'Fri, 13 Mar 2021 06:27:21 GMT')


    @patch('oss2.Session.do_request')
    def test_delete_bucket_style(self, do_request):
        request_text = '''DELETE /?style&styleName=imagestyle HTTP/1.1
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

        result = bucket().delete_bucket_style('imagestyle')

        self.assertRequest(req_info, request_text)


    @patch('oss2.Session.do_request')
    def test_put_black_referer(self, do_request):
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

<RefererConfiguration>
<AllowEmptyReferer>true</AllowEmptyReferer>
<RefererList>
<Referer>http://hello.com</Referer>
<Referer>mibrowser:home</Referer>
<Referer>{0}</Referer>
</RefererList>
<AllowTruncateQueryString>true</AllowTruncateQueryString>
<RefererBlacklist>
<Referer>http://hello2.com</Referer>
<Referer>mibrowser2:home</Referer>
<Referer>{1}</Referer>
</RefererBlacklist>
</RefererConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:46 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BE244ABFA2608E5A8AD'''

        req_info = mock_response(do_request, response_text)

        bucket().put_bucket_referer(BucketReferer(True, ['http://hello.com', 'mibrowser:home', '阿里巴巴'], True, ['http://hello2.com', 'mibrowser2:home', '阿里巴巴2']))

        self.assertRequest(req_info, request_text.format('阿里巴巴', '阿里巴巴2'))


    @patch('oss2.Session.do_request')
    def test_get_black_referer(self, do_request):
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
  <AllowTruncateQueryString>false</AllowTruncateQueryString>
  <RefererList>
    <Referer>http://hello.com</Referer>
    <Referer>mibrowser:home</Referer>
    <Referer>{0}</Referer>
  </RefererList>
  <RefererBlacklist>
    <Referer>http://www.aliyun.com</Referer>
    <Referer>mibrowser:home.com</Referer>
  </RefererBlacklist>
</RefererConfiguration>'''.format('阿里巴巴')

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_referer()

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.allow_empty_referer, True)
        self.assertEqual(result.allow_truncate_query_string, False)
        self.assertSortedListEqual(result.referers, ['http://hello.com', 'mibrowser:home', '阿里巴巴'])
        self.assertSortedListEqual(result.black_referers, ['http://www.aliyun.com', 'mibrowser:home.com'])


    @patch('oss2.Session.do_request')
    def test_get_black_referer2(self, do_request):
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
    def test_describe_regions(self, do_request):
        request_text = '''GET /?regions HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<RegionInfoList>
  <RegionInfo>
     <Region>oss-cn-hangzhou</Region>
     <InternetEndpoint>oss-cn-hangzhou.aliyuncs.com</InternetEndpoint>
     <InternalEndpoint>oss-cn-hangzhou-internal.aliyuncs.com</InternalEndpoint>
     <AccelerateEndpoint>oss-accelerate.aliyuncs.com</AccelerateEndpoint>  
  </RegionInfo>
  <RegionInfo>
     <Region>oss-cn-shanghai</Region>
     <InternetEndpoint>oss-cn-shanghai.aliyuncs.com</InternetEndpoint>
     <InternalEndpoint>oss-cn-shanghai-internal.aliyuncs.com</InternalEndpoint>
     <AccelerateEndpoint>oss-accelerate.aliyuncs.com</AccelerateEndpoint>  
  </RegionInfo>
</RegionInfoList>
'''

        req_info = mock_response(do_request, response_text)

        result = service().describe_regions()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.regions[0].region, 'oss-cn-hangzhou')
        self.assertEqual(result.regions[0].internet_endpoint, 'oss-cn-hangzhou.aliyuncs.com')
        self.assertEqual(result.regions[0].internal_endpoint, 'oss-cn-hangzhou-internal.aliyuncs.com')
        self.assertEqual(result.regions[0].accelerate_endpoint, 'oss-accelerate.aliyuncs.com')
        self.assertEqual(result.regions[1].region, 'oss-cn-shanghai')
        self.assertEqual(result.regions[1].internet_endpoint, 'oss-cn-shanghai.aliyuncs.com')
        self.assertEqual(result.regions[1].internal_endpoint, 'oss-cn-shanghai-internal.aliyuncs.com')
        self.assertEqual(result.regions[1].accelerate_endpoint, 'oss-accelerate.aliyuncs.com')

    @patch('oss2.Session.do_request')
    def test_async_process_object(self, do_request):
        request_text = '''POST /test-video.mp4?x-oss-async-process HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
x-oss-async-process=video/convert,f_mp4,vcodec_h265,s_1920x1080,vb_2000000,fps_30,acodec_aac,ab_100000,sn_1|sys/saveas
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****
'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:42 GMT
Content-Type: application/xml
Content-Length: 96
Connection: keep-alive
x-oss-request-id: 566B6BDD68248CE14F729DC0
x-oss-async-process=video/convert,f_mp4,vcodec_h265,s_1920x1080,vb_2000000,fps_30,acodec_aac,ab_100000,sn_1|sys/saveas

{"EventId":"3D7-1XxFtV2t3VtcOn2CXqI2ldsMN3i","RequestId":"8DF65942-D483-5E7E-BC1A-B25C617A9C32","TaskId":"MediaConvert-d2280366-cd33-48f7-90c6-a0dab65bed63"}
'''
        req_info = mock_response(do_request, response_text)
        key = "test-video.mp4"
        result = bucket().async_process_object(key, 'video/convert,f_mp4,vcodec_h265,s_1920x1080,vb_2000000,fps_30,acodec_aac,ab_100000,sn_1|sys/saveas')

        self.assertEqual(result.request_id, '566B6BDD68248CE14F729DC0')
        self.assertEqual(result.async_request_id, '8DF65942-D483-5E7E-BC1A-B25C617A9C32')
        self.assertEqual(result.event_id, '3D7-1XxFtV2t3VtcOn2CXqI2ldsMN3i')
        self.assertEqual(result.task_id, 'MediaConvert-d2280366-cd33-48f7-90c6-a0dab65bed63')


    @patch('oss2.Session.do_request')
    def test_put_bucket_callback_policy(self, do_request):
        request_text = '''PUT /?policy&comp=callback HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<BucketCallbackPolicy>
<PolicyItem>
<PolicyName>test_1</PolicyName>
<Callback>eyJjYWxsYmFja1VybCI6Ind3dy5hYmMuY29tL2NhbGxiYWNrIiwiY2FsbGJhY2tCb2R5IjoiJHtldGFnfSJ9=</Callback>
<CallbackVar/>
</PolicyItem>
<PolicyItem>
<PolicyName>{0}</PolicyName>
<Callback>{1}</Callback>
<CallbackVar>{2}</CallbackVar>
</PolicyItem>
</BucketCallbackPolicy>'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)
        policy_name = 'test_1'
        callback = 'eyJjYWxsYmFja1VybCI6Ind3dy5hYmMuY29tL2NhbGxiYWNrIiwiY2FsbGJhY2tCb2R5IjoiJHtldGFnfSJ9='
        policy_name2 = 'test_2'
        callback2 = 'eyJjYWxsYmFja1VybCI6Imh0dHA6Ly93d3cuYmJjVwiOiR7c2l6ZX19In0='
        callback_var2 = 'eyJ4OmEiOiJhIiwgIng6YiI6ImIifQ=='
        callback_policy_1 = CallbackPolicyInfo(policy_name, callback)
        callback_policy_2 = CallbackPolicyInfo(policy_name2, callback2, callback_var2)
        bucket().put_bucket_callback_policy([callback_policy_1, callback_policy_2])
        self.assertRequest(req_info, request_text.format(policy_name2, callback2, callback_var2))

    @patch('oss2.Session.do_request')
    def test_get_callback_policy(self, do_request):
        request_text = '''GET /?policy&comp=callback HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<BucketCallbackPolicy>
  <PolicyItem>
    <PolicyName>test_1</PolicyName>
    <Callback>eyJjYWxsYmFja1VybCI6Ind3dy5hYmMuY29tL2NhbGxiYWNrIiwiY2FsbGJhY2tCb2R5IjoiJHtldGFnfSJ9</Callback>
    <CallbackVar>eyJ4OnZhcjEiOiJ2YWx1ZTEiLCJ4OnZhcjIiOiJ2YWx1ZTIifQ==</CallbackVar>
  </PolicyItem>
  <PolicyItem>
    <PolicyName>test_2</PolicyName>
    <Callback>eyJjYWxsYmFja1VybCI6Imh0dHe1wibWltZVR5cGVcIjoke21pbWVUeXBlfSxcInNpemVcIjoke3NpemV9fSJ9</Callback>
    <CallbackVar>eyJ4OmEiOiJhIiwgIng6YiI6ImIifQ==</CallbackVar>
  </PolicyItem>
</BucketCallbackPolicy>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_callback_policy()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.callback_policies[0].policy_name, 'test_1')
        self.assertEqual(result.callback_policies[0].callback, 'eyJjYWxsYmFja1VybCI6Ind3dy5hYmMuY29tL2NhbGxiYWNrIiwiY2FsbGJhY2tCb2R5IjoiJHtldGFnfSJ9')
        self.assertEqual(result.callback_policies[0].callback_var, 'eyJ4OnZhcjEiOiJ2YWx1ZTEiLCJ4OnZhcjIiOiJ2YWx1ZTIifQ==')
        self.assertEqual(result.callback_policies[1].policy_name, 'test_2')
        self.assertEqual(result.callback_policies[1].callback, 'eyJjYWxsYmFja1VybCI6Imh0dHe1wibWltZVR5cGVcIjoke21pbWVUeXBlfSxcInNpemVcIjoke3NpemV9fSJ9')
        self.assertEqual(result.callback_policies[1].callback_var, 'eyJ4OmEiOiJhIiwgIng6YiI6ImIifQ==')


    @patch('oss2.Session.do_request')
    def test_delete_callback_policy(self, do_request):
        request_text = '''DELETE /?policy&comp=callback HTTP/1.1
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

        result = bucket().delete_bucket_callback_policy()

        self.assertRequest(req_info, request_text)


    @patch('oss2.Session.do_request')
    def test_list_buckets(self, do_request):
        request_text = '''GET /?prefix=my&max-keys=10 HTTP/1.1
Host: oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:38 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
x-oss-resource-group-id: rg-acfmxmt3***
authorization: OSS ZCDmm7TPZKHtx77j:Pt0DtPQ/FODOGs5y0yTIVctRcok='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:38 GMT
Content-Type: application/xml
Content-Length: 277
Connection: keep-alive
x-oss-resource-group-id: rg-acfmxmt3***
x-oss-request-id: 566B6BDA010B7A4314D1614A

<?xml version="1.0" encoding="UTF-8"?>
<ListAllMyBucketsResult>
  <Owner>
    <ID>512**</ID>
    <DisplayName>51264</DisplayName>
  </Owner>
  <Buckets>
    <Bucket>
      <CreationDate>2014-02-07T18:12:43.000Z</CreationDate>
      <ExtranetEndpoint>oss-cn-shanghai.aliyuncs.com</ExtranetEndpoint>
      <IntranetEndpoint>oss-cn-shanghai-internal.aliyuncs.com</IntranetEndpoint>
      <Location>oss-cn-shanghai</Location>
      <Name>test-bucket-1</Name>
      <Region>cn-shanghai</Region>
      <StorageClass>IA</StorageClass>
      <ResourceGroupId>rg-acfmxmt3***</ResourceGroupId>
    </Bucket>
    <Bucket>
      <CreationDate>2014-02-05T11:21:04.000Z</CreationDate>
      <ExtranetEndpoint>oss-cn-hangzhou.aliyuncs.com</ExtranetEndpoint>
      <IntranetEndpoint>oss-cn-hangzhou-internal.aliyuncs.com</IntranetEndpoint>
      <Location>oss-cn-hangzhou</Location>
      <Name>test-bucket-2</Name>
      <Region>cn-hangzhou</Region>
      <StorageClass>Standard</StorageClass>
      <ResourceGroupId>rg-***</ResourceGroupId>
    </Bucket>
  </Buckets>
</ListAllMyBucketsResult>'''

        req_info = mock_response(do_request, response_text)

        headers = dict()
        headers['x-oss-resource-group-id'] = 'rg-acfmxmt3***'
        result = service().list_buckets(prefix='my', max_keys=10, headers=headers)

        self.assertRequest(req_info, request_text)
        self.assertEqual("512**", result.owner.id)
        self.assertEqual("51264", result.owner.display_name)
        self.assertEqual("test-bucket-1", result.buckets[0].name)
        self.assertEqual("cn-shanghai", result.buckets[0].region)
        self.assertEqual("IA", result.buckets[0].storage_class)
        self.assertEqual("rg-acfmxmt3***", result.buckets[0].resource_group_id)
        self.assertEqual("oss-cn-shanghai", result.buckets[0].location)
        self.assertEqual(iso8601_to_unixtime("2014-02-07T18:12:43.000Z"), result.buckets[0].creation_date)
        self.assertEqual("oss-cn-shanghai.aliyuncs.com", result.buckets[0].extranet_endpoint)
        self.assertEqual("oss-cn-shanghai-internal.aliyuncs.com", result.buckets[0].intranet_endpoint)
        self.assertEqual("test-bucket-2", result.buckets[1].name)
        self.assertEqual("cn-hangzhou", result.buckets[1].region)
        self.assertEqual("Standard", result.buckets[1].storage_class)
        self.assertEqual("rg-***", result.buckets[1].resource_group_id)
        self.assertEqual("oss-cn-hangzhou", result.buckets[1].location)
        self.assertEqual(iso8601_to_unixtime("2014-02-05T11:21:04.000Z"), result.buckets[1].creation_date)
        self.assertEqual("oss-cn-hangzhou.aliyuncs.com", result.buckets[1].extranet_endpoint)
        self.assertEqual("oss-cn-hangzhou-internal.aliyuncs.com", result.buckets[1].intranet_endpoint)


    @patch('oss2.Session.do_request')
    def test_list_buckets_2(self, do_request):
        request_text = '''GET /?prefix=my&max-keys=10 HTTP/1.1
Host: oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:38 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
x-oss-resource-group-id: rg-acfmxmt3***
authorization: OSS ZCDmm7TPZKHtx77j:Pt0DtPQ/FODOGs5y0yTIVctRcok='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:38 GMT
Content-Type: application/xml
Content-Length: 277
Connection: keep-alive
x-oss-resource-group-id: rg-acfmxmt3***
x-oss-request-id: 566B6BDA010B7A4314D1614A

<?xml version="1.0" encoding="UTF-8"?>
<ListAllMyBucketsResult>
  <Buckets>
    <Bucket>
      <CreationDate>2014-02-07T18:12:43.000Z</CreationDate>
      <ExtranetEndpoint>oss-cn-shanghai.aliyuncs.com</ExtranetEndpoint>
      <IntranetEndpoint>oss-cn-shanghai-internal.aliyuncs.com</IntranetEndpoint>
      <Location>oss-cn-shanghai</Location>
      <Name>test-bucket-1</Name>
      <StorageClass>Standard</StorageClass>
    </Bucket>
  </Buckets>
</ListAllMyBucketsResult>'''

        req_info = mock_response(do_request, response_text)

        headers = dict()
        headers['x-oss-resource-group-id'] = 'rg-acfmxmt3***'
        result = service().list_buckets(prefix='my', max_keys=10, headers=headers)

        self.assertRequest(req_info, request_text)

        self.assertEqual("test-bucket-1", result.buckets[0].name)
        self.assertEqual("Standard", result.buckets[0].storage_class)
        self.assertEqual("oss-cn-shanghai", result.buckets[0].location)
        self.assertEqual(iso8601_to_unixtime("2014-02-07T18:12:43.000Z"), result.buckets[0].creation_date)
        self.assertEqual("oss-cn-shanghai.aliyuncs.com", result.buckets[0].extranet_endpoint)
        self.assertEqual("oss-cn-shanghai-internal.aliyuncs.com", result.buckets[0].intranet_endpoint)


    @patch('oss2.Session.do_request')
    def test_get_bucket_info(self, do_request):
        request_text = '''GET /?bucketInfo  HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<BucketInfo>
  <Bucket>
    <AccessMonitor>Enabled</AccessMonitor>
    <CreationDate>2013-07-31T10:56:21.000Z</CreationDate>
    <ExtranetEndpoint>oss-cn-hangzhou.aliyuncs.com</ExtranetEndpoint>
    <IntranetEndpoint>oss-cn-hangzhou-internal.aliyuncs.com</IntranetEndpoint>
    <Location>oss-cn-hangzhou</Location>
    <StorageClass>IA</StorageClass>
    <TransferAcceleration>Disabled</TransferAcceleration>
    <CrossRegionReplication>Disabled</CrossRegionReplication>
    <Name>oss-example</Name>
    <ResourceGroupId>rg-aek27tc********</ResourceGroupId>
    <Owner>
      <DisplayName>username</DisplayName>
      <ID>27183473914****</ID>
    </Owner>
    <AccessControlList>
      <Grant>private</Grant>
    </AccessControlList>  
    <Comment>test</Comment>
  </Bucket>
</BucketInfo>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_info()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.name, 'oss-example')
        self.assertEqual(result.owner.display_name, 'username')
        self.assertEqual(result.owner.id, '27183473914****')
        self.assertEqual(result.location, 'oss-cn-hangzhou')
        self.assertEqual(result.storage_class, 'IA')
        self.assertEqual(result.access_monitor, 'Enabled')
        self.assertEqual(result.creation_date, '2013-07-31T10:56:21.000Z')
        self.assertEqual(result.intranet_endpoint, 'oss-cn-hangzhou-internal.aliyuncs.com')
        self.assertEqual(result.extranet_endpoint, 'oss-cn-hangzhou.aliyuncs.com')
        self.assertEqual(result.transfer_acceleration, 'Disabled')
        self.assertEqual(result.cross_region_replication, 'Disabled')
        self.assertEqual(result.resource_group_id, 'rg-aek27tc********')
        self.assertEqual(result.acl.grant, 'private')
        self.assertEqual(result.comment, 'test')


    @patch('oss2.Session.do_request')
    def test_put_async_fetch_callback_failed(self, do_request):
        from oss2.compat import to_bytes
        from oss2.models import AsyncFetchTaskConfiguration
        request_text = '''POST /?asyncFetch HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<AsyncFetchTaskConfiguration>
<Url>www.test.com/abc.txt</Url>
<Object>abc.txt</Object>
<Host>www.test.com</Host>
<ContentMD5>v23MlMRM/EgJczOs2yHTcA==</ContentMD5>
<Callback>eyJjYWxsYmFja1VybCI6Ind3dy5hYmMuY29tL2NhbGxiYWNrIiwiY2FsbGJhY2tCb2R5IjoiJHtldGFnfSJ9</Callback>
<IgnoreSameKey>true</IgnoreSameKey>
<CallbackWhenFailed>{0}</CallbackWhenFailed>
</AsyncFetchTaskConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<AsyncFetchTaskResult>
    <TaskId>26546</TaskId>
</AsyncFetchTaskResult>'''


        req_info = mock_response(do_request, response_text)
        object_name ='abc.txt'
        host = 'www.test.com'
        content_md5 = 'v23MlMRM/EgJczOs2yHTcA=='
        ignore_same_key = True
        callback = '{"callbackUrl":"www.abc.com/callback","callbackBody":"${etag}"}'
        base64_callback = oss2.utils.b64encode_as_string(to_bytes(callback))
        callback_when_failed = True
        task_config = AsyncFetchTaskConfiguration('www.test.com/abc.txt', object_name=object_name, host=host, content_md5=content_md5, callback=base64_callback, ignore_same_key=ignore_same_key, callback_when_failed=callback_when_failed)
        bucket().put_async_fetch_task(task_config)
        self.assertRequest(req_info, request_text.format(str(callback_when_failed).lower()))


    @patch('oss2.Session.do_request')
    def test_path_style(self, do_request):
        request_text = '''DELETE /ming-oss-share/?policy&comp=callback HTTP/1.1
Host: oss-cn-hangzhou.aliyuncs.com
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
        bucket = oss2.Bucket(oss2.Auth('fake-access-key-id', 'fake-access-key-secret'),
                             'http://oss-cn-hangzhou.aliyuncs.com', BUCKET_NAME, is_path_style=True)
        result = bucket.delete_bucket_callback_policy()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.status, 204)


    @patch('oss2.Session.do_request')
    def test_write_get_object_response(self, do_request):
        request_text = '''POST /?x-oss-write-get-object-response HTTP/1.1
Host: oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:41 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Pt0DtPQ/FODOGs5y0yTIVctRcok=

123'''

        response_text = '''HTTP/1.1 204 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:42 GMT
Content-Type: application/xml
Connection: keep-alive
x-oss-request-id: 566B6BDD68248CE14F729DC0
'''
        req_info = mock_response(do_request, response_text)

        route = 'test-ap-process-name-1283******516515-opap.oss-cn-beijing-internal.oss-object-process.aliyuncs.com'
        token = 'OSSV1#UMoA43+Bi9b6Q1Lu6UjhLXnmq4I/wIFac3uZfBkgJtg2xtHkZJ4bZglDWyOgWRlGTrA8y/i6D9eH8PmAiq2NL2R/MD/UX6zvRhT8WMHUewgc9QWPs9LPHiZytkUZnGa39mnv/73cyPWTuxgxyk4dNhlzEE6U7PdzmCCu8gIrjuYLPrA9psRn0ZC8J2/DCZGVx0BE7AmIJTcNtLKTSjxsJyTts/******'
        fwd_status = '200'
        content = '123'
        headers = dict()
        headers['x-oss-fwd-header-Content-Type'] = 'application/octet-stream'
        headers['x-oss-fwd-header-ETag'] = 'testetag'

        result = service().write_get_object_response(route, token, fwd_status, content, headers)

        self.assertRequest(req_info, request_text)

    def test_is_verify_object_strict_flag(self):
        auth = oss2.Auth('fake-access-key-id', 'fake-access-key-secret')
        bucket = oss2.Bucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', "bucket")
        self.assertTrue(bucket.is_verify_object_strict)

        key = '?123.txt'
        try:
            bucket.sign_url('PUT', key, 1650801600)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: The key cannot start with `?`, please check it.')

        key = '?'
        try:
            bucket.sign_url('PUT', key, 1650801600)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: The key cannot start with `?`, please check it.')

        auth = oss2.AuthV2('fake-access-key-id', 'fake-access-key-secret')
        bucket = oss2.Bucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', "bucket")
        self.assertFalse(bucket.is_verify_object_strict)
        key = '?123.txt'
        url = bucket.sign_url('PUT', key, 1650801600)
        self.assertTrue(url.find('%3F123.txt') != -1)
        key = '?'
        self.assertTrue(url.find('%3F') != -1)

        auth = oss2.AuthV4('fake-access-key-id', 'fake-access-key-secret')
        bucket = oss2.Bucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', "bucket", region='cn-hangzhou')
        self.assertFalse(bucket.is_verify_object_strict)
        key = '?123.txt'
        url = bucket.sign_url('PUT', key, 1650801600)
        self.assertTrue(url.find('%3F123.txt') != -1)
        key = '?'
        self.assertTrue(url.find('%3F') != -1)

        bucket = oss2.Bucket('', 'http://oss-cn-hangzhou.aliyuncs.com', "bucket")
        self.assertTrue(bucket.is_verify_object_strict)

    @patch('oss2.Session.do_request')
    def test_put_bucket_archive_direct_read(self, do_request):
        request_text = '''PUT /?bucketArchiveDirectRead HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<ArchiveDirectReadConfiguration><Enabled>true</Enabled></ArchiveDirectReadConfiguration>
'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)

        result = bucket().put_bucket_archive_direct_read(True)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '5C1B138A109F4E405B2D')
        self.assertEqual(result.status, 200)


    @patch('oss2.Session.do_request')
    def test_get_bucket_archive_direct_read(self, do_request):
        request_text = '''GET /?bucketArchiveDirectRead HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<ArchiveDirectReadConfiguration>
<Enabled>false</Enabled>
</ArchiveDirectReadConfiguration>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_archive_direct_read()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.enabled, False)

    @patch('oss2.Session.do_request')
    def test_put_bucket_https_config(self, do_request):

        request_text = '''PUT /?httpsConfig= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 249
date: Sat, 12 Dec 2015 00:35:46 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Kq2RS9nmT44C1opXGbcLzNdTt1A=

<HttpsConfiguration><TLS><Enable>true</Enable><TLSVersion>TLSv1.2</TLSVersion><TLSVersion>TLSv1.3</TLSVersion></TLS></HttpsConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:46 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BE244ABFA2608E5A8AD'''

        req_info = mock_response(do_request, response_text)

        bucket().put_bucket_https_config(BucketTlsVersion(True, ['TLSv1.2', 'TLSv1.3']))

        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_get_bucket_https_config(self, do_request):
        request_text = '''GET /?httpsConfig= HTTP/1.1
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
<HttpsConfiguration>
  <TLS>
    <Enable>true</Enable>
    <TLSVersion>TLSv1.2</TLSVersion>
    <TLSVersion>TLSv1.3</TLSVersion>
  </TLS>
</HttpsConfiguration>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_https_config()

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.tls_enabled, True)
        self.assertSortedListEqual(result.tls_version, ['TLSv1.2', 'TLSv1.3'])


    @patch('oss2.Session.do_request')
    def test_create_bucket_data_redundancy_transition(self, do_request):
        request_text = '''POST /?redundancyTransition&x-oss-target-redundancy-type=ZRS HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
date: Wed, 15 Sep 2021 03:33:37 GMT

<?xml version="1.0" encoding="UTF-8"?>
<BucketDataRedundancyTransition>
  <TaskId>4be5beb0f74f490186311b268bf6****</TaskId>
</BucketDataRedundancyTransition>'''

        req_info = mock_response(do_request, response_text)
        target_type = "ZRS"
        result = bucket().create_bucket_data_redundancy_transition(target_type)
        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '5C1B138A109F4E405B2D')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.task_id, '4be5beb0f74f490186311b268bf6****')

    @patch('oss2.Session.do_request')
    def test_get_bucket_data_redundancy_transition(self, do_request):
        request_text = '''GET /?redundancyTransition&x-oss-redundancy-transition-taskid=8bf6**** HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<BucketDataRedundancyTransition>
  <Bucket>examplebucket</Bucket>
  <TaskId>909c6c818dd041d1a44e0fdc66aa****</TaskId>
  <Status>Finished</Status>
  <CreateTime>2023-11-17T09:14:39.000Z</CreateTime>
  <StartTime>2023-11-17T09:14:39.000Z</StartTime>
  <ProcessPercentage>100</ProcessPercentage>
  <EstimatedRemainingTime>122</EstimatedRemainingTime>
  <EndTime>2023-11-18T09:14:39.000Z</EndTime>
</BucketDataRedundancyTransition>'''

        req_info = mock_response(do_request, response_text)

        task_id = "8bf6****"
        result = bucket().get_bucket_data_redundancy_transition(task_id)
        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.bucket, 'examplebucket')
        self.assertEqual(result.task_id, '909c6c818dd041d1a44e0fdc66aa****')
        self.assertEqual(result.transition_status, 'Finished')
        self.assertEqual(result.create_time, '2023-11-17T09:14:39.000Z')
        self.assertEqual(result.start_time, '2023-11-17T09:14:39.000Z')
        self.assertEqual(result.end_time, '2023-11-18T09:14:39.000Z')
        self.assertEqual(result.process_percentage, 100)
        self.assertEqual(result.estimated_remaining_time, 122)


    @patch('oss2.Session.do_request')
    def test_list_user_data_redundancy_transition(self, do_request):
        request_text = '''GET /?redundancyTransition&continuation-token=123xxx&max-keys=10 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<ListBucketDataRedundancyTransition>
  <IsTruncated>false</IsTruncated>
  <NextContinuationToken>6GHUGkjoXXX***l53245</NextContinuationToken>
  <BucketDataRedundancyTransition>
    <Bucket>examplebucket1</Bucket>
    <TaskId>4be5beb0f74f490186311b268bf6****</TaskId>
    <Status>Queueing</Status>
    <CreateTime>2023-11-17T08:40:17.000Z</CreateTime>
  </BucketDataRedundancyTransition>
  <BucketDataRedundancyTransition>
    <Bucket>examplebucket3</Bucket>
    <TaskId>4be5beb0er4f490186311b268bf6j****</TaskId>
    <Status>Finished</Status>
    <CreateTime>2023-11-17T08:40:17.000Z</CreateTime>
    <StartTime>2023-11-17T11:40:18.000Z</StartTime>
    <ProcessPercentage>123453</ProcessPercentage>
    <EstimatedRemainingTime>12345</EstimatedRemainingTime>
    <EndTime>2023-11-18T09:40:17.000Z</EndTime>
  </BucketDataRedundancyTransition>
</ListBucketDataRedundancyTransition>'''

        req_info = mock_response(do_request, response_text)

        result = service().list_user_data_redundancy_transition(continuation_token='123xxx', max_keys=10)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.is_truncated, False)
        self.assertEqual(result.next_continuation_token, '6GHUGkjoXXX***l53245')
        self.assertEqual(result.data_redundancy_transitions[0].bucket, 'examplebucket1')
        self.assertEqual(result.data_redundancy_transitions[0].transition_status, 'Queueing')
        self.assertEqual(result.data_redundancy_transitions[0].create_time, '2023-11-17T08:40:17.000Z')

        self.assertEqual(result.data_redundancy_transitions[1].task_id, '4be5beb0er4f490186311b268bf6j****')
        self.assertEqual(result.data_redundancy_transitions[1].bucket, 'examplebucket3')
        self.assertEqual(result.data_redundancy_transitions[1].transition_status, 'Finished')
        self.assertEqual(result.data_redundancy_transitions[1].create_time, '2023-11-17T08:40:17.000Z')
        self.assertEqual(result.data_redundancy_transitions[1].start_time, '2023-11-17T11:40:18.000Z')
        self.assertEqual(result.data_redundancy_transitions[1].end_time, '2023-11-18T09:40:17.000Z')
        self.assertEqual(result.data_redundancy_transitions[1].process_percentage, 123453)
        self.assertEqual(result.data_redundancy_transitions[1].estimated_remaining_time, 12345)


    @patch('oss2.Session.do_request')
    def test_list_bucket_data_redundancy_transition(self, do_request):
        request_text = '''GET /?redundancyTransition HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<ListBucketDataRedundancyTransition>
  <BucketDataRedundancyTransition>
    <Bucket>examplebucket1</Bucket>
    <TaskId>4be5beb0f74f490186311b268bf6****</TaskId>
    <Status>Queueing</Status>
    <CreateTime>2023-11-17T08:40:17.000Z</CreateTime>
  </BucketDataRedundancyTransition>
  <BucketDataRedundancyTransition>
    <Bucket>examplebucket3</Bucket>
    <TaskId>4be5beb0er4f490186311b268bf6j****</TaskId>
    <Status>Finished</Status>
    <CreateTime>2023-11-17T08:40:17.000Z</CreateTime>
    <StartTime>2023-11-17T11:40:18.000Z</StartTime>
    <ProcessPercentage>123453</ProcessPercentage>
    <EstimatedRemainingTime>12345</EstimatedRemainingTime>
    <EndTime>2023-11-18T09:40:17.000Z</EndTime>
  </BucketDataRedundancyTransition>
</ListBucketDataRedundancyTransition>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().list_bucket_data_redundancy_transition()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.data_redundancy_transitions[0].task_id, '4be5beb0f74f490186311b268bf6****')
        self.assertEqual(result.data_redundancy_transitions[0].bucket, 'examplebucket1')
        self.assertEqual(result.data_redundancy_transitions[0].transition_status, 'Queueing')
        self.assertEqual(result.data_redundancy_transitions[0].create_time, '2023-11-17T08:40:17.000Z')

        self.assertEqual(result.data_redundancy_transitions[1].task_id, '4be5beb0er4f490186311b268bf6j****')
        self.assertEqual(result.data_redundancy_transitions[1].bucket, 'examplebucket3')
        self.assertEqual(result.data_redundancy_transitions[1].transition_status, 'Finished')
        self.assertEqual(result.data_redundancy_transitions[1].create_time, '2023-11-17T08:40:17.000Z')
        self.assertEqual(result.data_redundancy_transitions[1].start_time, '2023-11-17T11:40:18.000Z')
        self.assertEqual(result.data_redundancy_transitions[1].end_time, '2023-11-18T09:40:17.000Z')
        self.assertEqual(result.data_redundancy_transitions[1].process_percentage, 123453)
        self.assertEqual(result.data_redundancy_transitions[1].estimated_remaining_time, 12345)


    @patch('oss2.Session.do_request')
    def test_delete_bucket_data_redundancy_transition(self, do_request):
        request_text = '''DELETE /?redundancyTransition&x-oss-redundancy-transition-taskid=1231xxx HTTP/1.1
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

        result = bucket().delete_bucket_data_redundancy_transition('1231xxx')

        self.assertRequest(req_info, request_text)


    @patch('oss2.Session.do_request')
    def test_get_stat_deep_cold_archive(self, do_request):
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
    <ColdArchiveRealStorage>360</ColdArchiveRealStorage>
    <ColdArchiveObjectCount>36</ColdArchiveObjectCount>
    <DeepColdArchiveStorage>2359296</DeepColdArchiveStorage>
    <DeepColdArchiveRealStorage>370</DeepColdArchiveRealStorage>
    <DeepColdArchiveObjectCount>37</DeepColdArchiveObjectCount>
    <MultipartPartCount>4</MultipartPartCount>
    <DeleteMarkerCount>164</DeleteMarkerCount>
</BucketStat>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_stat()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.storage_size_in_bytes, 472594058)
        self.assertEqual(result.object_count, 666)
        self.assertEqual(result.multi_part_upload_count, 992)
        self.assertEqual(result.archive_real_storage, None)
        self.assertEqual(result.archive_object_count, None)
        self.assertEqual(result.cold_archive_real_storage, 360)
        self.assertEqual(result.cold_archive_object_count, 36)
        self.assertEqual(result.deep_cold_archive_storage, 2359296)
        self.assertEqual(result.deep_cold_archive_real_storage, 370)
        self.assertEqual(result.deep_cold_archive_object_count, 37)


    @patch('oss2.Session.do_request')
    def test_create_access_point(self, do_request):
        request_text = '''PUT /?accessPoint HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<CreateAccessPointConfiguration>
<AccessPointName>test-ap-jt-3</AccessPointName>
<NetworkOrigin>internet</NetworkOrigin>
<VpcConfiguration>
<VpcId>vpc-id</VpcId>
</VpcConfiguration>
</CreateAccessPointConfiguration>'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<CreateAccessPointResult>
<AccessPointArn>acs:oss:RegionId:OwnerId:accesspoint/ApName</AccessPointArn>
<Alias>ApAliasName</Alias>
</CreateAccessPointResult>'''

        req_info = mock_response(do_request, response_text)

        vpc = AccessPointVpcConfiguration('vpc-id')
        access_point = CreateAccessPointRequest('test-ap-jt-3', 'internet', vpc)
        result = bucket().create_access_point(access_point)
        self.assertRequest(req_info, request_text)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.access_point_arn, 'acs:oss:RegionId:OwnerId:accesspoint/ApName')
        self.assertEqual(result.alias, 'ApAliasName')

    @patch('oss2.Session.do_request')
    def test_get_access_point(self, do_request):
        request_text = '''GET /?accessPoint HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<GetAccessPointResult>
  <AccessPointName>test-ap-jt-3</AccessPointName>
  <Bucket>test-jt-ap-3</Bucket>
  <AccountId>aaabbb</AccountId>
  <NetworkOrigin>Internet</NetworkOrigin>
  <VpcConfiguration>
     <VpcId>vpc-id</VpcId>
  </VpcConfiguration>
  <AccessPointArn>arn:aws:s3:us-east-1:920305101104:accesspoint/test-ap-jt-3</AccessPointArn>
  <CreationDate>2022-01-05T05:39:53+00:00</CreationDate>
  <Alias>test-ap-jt-3-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias</Alias>
  <Status>enable</Status>
  <Endpoints>
    <PublicEndpoint>s3-accesspoint-fips.dualstack.us-east-1.amazonaws.com</PublicEndpoint>
    <InternalEndpoint>s3-accesspoint.dualstack.us-east-1.amazonaws.com</InternalEndpoint>
  </Endpoints>
</GetAccessPointResult>'''

        req_info = mock_response(do_request, response_text)

        accessPointName = 'test-ap-jt-3'
        result = bucket().get_access_point(accessPointName)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.access_point_name, "test-ap-jt-3")
        self.assertEqual(result.bucket, "test-jt-ap-3")
        self.assertEqual(result.account_id, "aaabbb")
        self.assertEqual(result.network_origin, "Internet")
        self.assertEqual(result.vpc.vpc_id, "vpc-id")
        self.assertEqual(result.access_point_arn, "arn:aws:s3:us-east-1:920305101104:accesspoint/test-ap-jt-3")
        self.assertEqual(result.creation_date, "2022-01-05T05:39:53+00:00")
        self.assertEqual(result.alias, "test-ap-jt-3-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias")
        self.assertEqual(result.access_point_status, "enable")
        self.assertEqual(result.endpoints.public_endpoint, "s3-accesspoint-fips.dualstack.us-east-1.amazonaws.com")
        self.assertEqual(result.endpoints.internal_endpoint, "s3-accesspoint.dualstack.us-east-1.amazonaws.com")


    @patch('oss2.Session.do_request')
    def test_delete_access_point(self, do_request):
        request_text = '''DELETE /?accessPoint HTTP/1.1
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

        accessPointName = 'test-ap-jt-3'
        result = bucket().delete_access_point(accessPointName)

        self.assertRequest(req_info, request_text)


    @patch('oss2.Session.do_request')
    def test_list_bucket_access_points(self, do_request):
        request_text = '''GET /?accessPoint&max-keys=10&continuation-token=abcd HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:38 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Pt0DtPQ/FODOGs5y0yTIVctRcok='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:38 GMT
Content-Type: application/xml
Content-Length: 277
Connection: keep-alive
x-oss-request-id: 566B6BDA010B7A4314D1614A

<ListAccessPointsResult>
    <IsTruncated>true</IsTruncated>
    <NextContinuationToken>sdfasfsagqeqg</NextContinuationToken>
    <AccountId>aaabbb</AccountId>
    <MaxKeys>10</MaxKeys>
    <Marker>marker</Marker>
    <AccessPoints>
        <AccessPoint>
            <Bucket>Bucket</Bucket>
            <AccessPointName>AccessPointName</AccessPointName>
            <Alias>test-ap-jt-1-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias</Alias>
            <NetworkOrigin>Internet</NetworkOrigin>
            <VpcConfiguration>
                <VpcId>vpc-id</VpcId>
            </VpcConfiguration>
            <Status>false</Status>
        </AccessPoint>
        <AccessPoint>
            <Bucket>Bucket2</Bucket>
            <AccessPointName>AccessPointName2</AccessPointName>
            <Alias>test-ap-jt-2-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias</Alias>
            <NetworkOrigin>Public</NetworkOrigin>
            <VpcConfiguration>
                <VpcId>vpc-id-2</VpcId>
            </VpcConfiguration>
            <Status>true</Status>
        </AccessPoint>
    </AccessPoints>
</ListAccessPointsResult>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().list_bucket_access_points(max_keys=10, continuation_token='abcd')

        self.assertRequest(req_info, request_text)
        self.assertEqual("aaabbb", result.account_id)
        self.assertEqual(10, result.max_keys)
        self.assertEqual(True, result.is_truncated)
        self.assertEqual("sdfasfsagqeqg", result.next_continuation_token)
        self.assertEqual("marker", result.marker)
        self.assertEqual("AccessPointName", result.access_points[0].access_point_name)
        self.assertEqual("Bucket", result.access_points[0].bucket)
        self.assertEqual("Internet", result.access_points[0].network_origin)
        self.assertEqual("test-ap-jt-1-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias", result.access_points[0].alias)
        self.assertEqual("false", result.access_points[0].status)
        self.assertEqual("vpc-id", result.access_points[0].vpc.vpc_id)
        self.assertEqual("AccessPointName2", result.access_points[1].access_point_name)
        self.assertEqual("Bucket2", result.access_points[1].bucket)
        self.assertEqual("Public", result.access_points[1].network_origin)
        self.assertEqual("test-ap-jt-2-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias", result.access_points[1].alias)
        self.assertEqual('true', result.access_points[1].status)
        self.assertEqual("vpc-id-2", result.access_points[1].vpc.vpc_id)


    @patch('oss2.Session.do_request')
    def test_list_access_points(self, do_request):
        request_text = '''GET /?accessPoint&max-keys=10&continuation-token=abcd HTTP/1.1
Host: oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:38 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Pt0DtPQ/FODOGs5y0yTIVctRcok='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:38 GMT
Content-Type: application/xml
Content-Length: 277
Connection: keep-alive
x-oss-request-id: 566B6BDA010B7A4314D1614A

<ListAccessPointsResult>
    <IsTruncated>true</IsTruncated>
    <NextContinuationToken>sdfasfsagqeqg</NextContinuationToken>
    <AccountId>aaabbb</AccountId>
    <MaxKeys>10</MaxKeys>
    <Marker>marker</Marker>
    <AccessPoints>
        <AccessPoint>
            <Bucket>Bucket</Bucket>
            <AccessPointName>AccessPointName</AccessPointName>
            <Alias>test-ap-jt-1-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias</Alias>
            <NetworkOrigin>Internet</NetworkOrigin>
            <VpcConfiguration>
                <VpcId>vpc-id</VpcId>
            </VpcConfiguration>
            <Status>false</Status>
        </AccessPoint>
        <AccessPoint>
            <Bucket>Bucket2</Bucket>
            <AccessPointName>AccessPointName2</AccessPointName>
            <Alias>test-ap-jt-2-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias</Alias>
            <NetworkOrigin>Public</NetworkOrigin>
            <VpcConfiguration>
                <VpcId>vpc-id-2</VpcId>
            </VpcConfiguration>
            <Status>true</Status>
        </AccessPoint>
    </AccessPoints>
</ListAccessPointsResult>'''

        req_info = mock_response(do_request, response_text)

        result = service().list_access_points(max_keys=10, continuation_token='abcd')

        self.assertRequest(req_info, request_text)
        self.assertEqual("aaabbb", result.account_id)
        self.assertEqual(10, result.max_keys)
        self.assertEqual(True, result.is_truncated)
        self.assertEqual("sdfasfsagqeqg", result.next_continuation_token)
        self.assertEqual("marker", result.marker)
        self.assertEqual("AccessPointName", result.access_points[0].access_point_name)
        self.assertEqual("Bucket", result.access_points[0].bucket)
        self.assertEqual("Internet", result.access_points[0].network_origin)
        self.assertEqual("test-ap-jt-1-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias", result.access_points[0].alias)
        self.assertEqual("false", result.access_points[0].status)
        self.assertEqual("vpc-id", result.access_points[0].vpc.vpc_id)
        self.assertEqual("AccessPointName2", result.access_points[1].access_point_name)
        self.assertEqual("Bucket2", result.access_points[1].bucket)
        self.assertEqual("Public", result.access_points[1].network_origin)
        self.assertEqual("test-ap-jt-2-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias", result.access_points[1].alias)
        self.assertEqual('true', result.access_points[1].status)
        self.assertEqual("vpc-id-2", result.access_points[1].vpc.vpc_id)


    @patch('oss2.Session.do_request')
    def test_put_access_point_policy(self, do_request):
        request_text = '''PUT /?accessPointPolicy HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

{"Version":"1","Statement":[{"Action":["oss:PutObject","oss:GetObject"],"Effect":"Deny","Principal":["1234567890"],"Resource":["acs:oss:cn-hangzhou:1234567890:accesspoint/$apName","acs:oss:cn-hangzhou:1234567890:accesspoint/$apName/object/*",]}]}'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT
'''

        req_info = mock_response(do_request, response_text)
        accessPointName = 'test-ap-jt-3'
        policy = '{"Version":"1","Statement":[{"Action":["oss:PutObject","oss:GetObject"],"Effect":"Deny","Principal":["1234567890"],"Resource":["acs:oss:cn-hangzhou:1234567890:accesspoint/$apName","acs:oss:cn-hangzhou:1234567890:accesspoint/$apName/object/*",]}]}'

        result = bucket().put_access_point_policy(accessPointName, policy)
        self.assertRequest(req_info, request_text)


    @patch('oss2.Session.do_request')
    def test_get_access_point_policy(self, do_request):
        request_text = '''GET /?accessPointPolicy HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:41 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Pt0DtPQ/FODOGs5y0yTIVctRcok='''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

{"Version":"1","Statement":[{"Action":["oss:PutObject","oss:GetObject"],"Effect":"Deny","Principal":["1234567890"],"Resource":["acs:oss:cn-hangzhou:1234567890:accesspoint/$apName","acs:oss:cn-hangzhou:1234567890:accesspoint/$apName/object/*",]}]}'''

        req_info = mock_response(do_request, response_text)
        policy = '{"Version":"1","Statement":[{"Action":["oss:PutObject","oss:GetObject"],"Effect":"Deny","Principal":["1234567890"],"Resource":["acs:oss:cn-hangzhou:1234567890:accesspoint/$apName","acs:oss:cn-hangzhou:1234567890:accesspoint/$apName/object/*",]}]}'
        aaaaaa = '{"Version":"1","Statement":[{"Action":["oss:PutObject","oss:GetObject"],"Effect":"Deny","Principal":["1234567890"],"Resource":["acs:oss:cn-hangzhou:1234567890:accesspoint/$apName","acs:oss:cn-hangzhou:1234567890:accesspoint/$apName/object/*",]}]}'
        accessPointName = 'test-ap-jt-3'
        result = bucket().get_access_point_policy(accessPointName)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.policy, policy)


    @patch('oss2.Session.do_request')
    def test_delete_access_point_policy(self, do_request):
        request_text = '''DELETE /?accessPointPolicy HTTP/1.1
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

        accessPointName = 'test-ap-jt-3'
        result = bucket().delete_access_point_policy(accessPointName)

        self.assertRequest(req_info, request_text)


    @patch('oss2.Session.do_request')
    def test_put_public_access_block(self, do_request):
        request_text = '''PUT /?publicAccessBlock HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<PublicAccessBlockConfiguration>
<BlockPublicAccess>True</BlockPublicAccess>
</PublicAccessBlockConfiguration>
'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)

        result = service().put_public_access_block(True)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '5C1B138A109F4E405B2D')
        self.assertEqual(result.status, 200)


    @patch('oss2.Session.do_request')
    def test_get_public_access_block(self, do_request):
        request_text = '''GET /?publicAccessBlock HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<PublicAccessBlockConfiguration>
  <BlockPublicAccess>true</BlockPublicAccess>
</PublicAccessBlockConfiguration>'''

        req_info = mock_response(do_request, response_text)

        result = service().get_public_access_block()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(True, result.block_public_access)

    @patch('oss2.Session.do_request')
    def test_get_public_access_block_invalid(self, do_request):
        request_text = '''GET /?publicAccessBlock HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<PublicAccessBlockConfiguration>
</PublicAccessBlockConfiguration>'''

        req_info = mock_response(do_request, response_text)

        result = service().get_public_access_block()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(None, result.block_public_access)


    @patch('oss2.Session.do_request')
    def test_delete_public_access_block(self, do_request):
        request_text = '''DELETE /?publicAccessBlock HTTP/1.1
Host: oss-cn-hangzhou.aliyuncs.com
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

        result = service().delete_public_access_block()

        self.assertRequest(req_info, request_text)


    @patch('oss2.Session.do_request')
    def test_put_bucket_public_access_block(self, do_request):
        request_text = '''PUT /?publicAccessBlock HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<PublicAccessBlockConfiguration>
<BlockPublicAccess>True</BlockPublicAccess>
</PublicAccessBlockConfiguration>
'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)

        result = bucket().put_bucket_public_access_block(True)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '5C1B138A109F4E405B2D')
        self.assertEqual(result.status, 200)


    @patch('oss2.Session.do_request')
    def test_get_bucket_public_access_block(self, do_request):
        request_text = '''GET /?publicAccessBlock HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<PublicAccessBlockConfiguration>
  <BlockPublicAccess>true</BlockPublicAccess>
</PublicAccessBlockConfiguration>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_public_access_block()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(True, result.block_public_access)


    @patch('oss2.Session.do_request')
    def test_get_bucket_public_access_block_invalid(self, do_request):
        request_text = '''GET /?publicAccessBlock HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<PublicAccessBlockConfiguration>

</PublicAccessBlockConfiguration>'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_public_access_block()

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(None, result.block_public_access)


    @patch('oss2.Session.do_request')
    def test_delete_bucket_public_access_block(self, do_request):
        request_text = '''DELETE /?publicAccessBlock HTTP/1.1
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

        result = bucket().delete_bucket_public_access_block()

        self.assertRequest(req_info, request_text)


    @patch('oss2.Session.do_request')
    def test_put_access_point_public_access_block(self, do_request):
        request_text = '''PUT /?publicAccessBlock&x-oss-access-point-name=ap-01 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<PublicAccessBlockConfiguration>
<BlockPublicAccess>True</BlockPublicAccess>
</PublicAccessBlockConfiguration>
'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)

        access_point_name='ap-01'
        result = bucket().put_access_point_public_access_block(access_point_name,True)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '5C1B138A109F4E405B2D')
        self.assertEqual(result.status, 200)


    @patch('oss2.Session.do_request')
    def test_get_access_point_public_access_block(self, do_request):
        request_text = '''GET /?publicAccessBlock&x-oss-access-point-name=ap-01 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<PublicAccessBlockConfiguration>
  <BlockPublicAccess>true</BlockPublicAccess>
</PublicAccessBlockConfiguration>'''

        req_info = mock_response(do_request, response_text)

        access_point_name='ap-01'
        result = bucket().get_access_point_public_access_block(access_point_name)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(True, result.block_public_access)


    @patch('oss2.Session.do_request')
    def test_get_access_point_public_access_block_invalid(self, do_request):
        request_text = '''GET /?publicAccessBlock&x-oss-access-point-name=ap-01 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<PublicAccessBlockConfiguration>

</PublicAccessBlockConfiguration>'''

        req_info = mock_response(do_request, response_text)

        access_point_name='ap-01'
        result = bucket().get_access_point_public_access_block(access_point_name)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(None, result.block_public_access)


    @patch('oss2.Session.do_request')
    def test_delete_access_point_public_access_block(self, do_request):
        request_text = '''DELETE /?publicAccessBlock&x-oss-access-point-name=ap-01 HTTP/1.1
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

        access_point_name='ap-01'
        result = bucket().delete_access_point_public_access_block(access_point_name)

        self.assertRequest(req_info, request_text)


    @patch('oss2.Session.do_request')
    def test_get_access_point_with_block(self, do_request):
        request_text = '''GET /?accessPoint HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<GetAccessPointResult>
  <AccessPointName>test-ap-jt-3</AccessPointName>
  <Bucket>test-jt-ap-3</Bucket>
  <AccountId>aaabbb</AccountId>
  <NetworkOrigin>Internet</NetworkOrigin>
  <VpcConfiguration>
     <VpcId>vpc-id</VpcId>
  </VpcConfiguration>
  <AccessPointArn>arn:aws:s3:us-east-1:920305101104:accesspoint/test-ap-jt-3</AccessPointArn>
  <CreationDate>2022-01-05T05:39:53+00:00</CreationDate>
  <Alias>test-ap-jt-3-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias</Alias>
  <Status>enable</Status>
  <Endpoints>
    <PublicEndpoint>s3-accesspoint-fips.dualstack.us-east-1.amazonaws.com</PublicEndpoint>
    <InternalEndpoint>s3-accesspoint.dualstack.us-east-1.amazonaws.com</InternalEndpoint>
  </Endpoints>
  <PublicAccessBlockConfiguration>
    <BlockPublicAccess>true</BlockPublicAccess>
  </PublicAccessBlockConfiguration>
</GetAccessPointResult>'''

        req_info = mock_response(do_request, response_text)

        accessPointName = 'test-ap-jt-3'
        result = bucket().get_access_point(accessPointName)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.access_point_name, "test-ap-jt-3")
        self.assertEqual(result.bucket, "test-jt-ap-3")
        self.assertEqual(result.account_id, "aaabbb")
        self.assertEqual(result.network_origin, "Internet")
        self.assertEqual(result.vpc.vpc_id, "vpc-id")
        self.assertEqual(result.access_point_arn, "arn:aws:s3:us-east-1:920305101104:accesspoint/test-ap-jt-3")
        self.assertEqual(result.creation_date, "2022-01-05T05:39:53+00:00")
        self.assertEqual(result.alias, "test-ap-jt-3-pi1kg766wz34gwij4oan1tkep38gwuse1a-s3alias")
        self.assertEqual(result.access_point_status, "enable")
        self.assertEqual(result.endpoints.public_endpoint, "s3-accesspoint-fips.dualstack.us-east-1.amazonaws.com")
        self.assertEqual(result.endpoints.internal_endpoint, "s3-accesspoint.dualstack.us-east-1.amazonaws.com")
        self.assertEqual(result.endpoints.public_endpoint, "s3-accesspoint-fips.dualstack.us-east-1.amazonaws.com")
        self.assertEqual(result.public_access_block_configuration.block_public_access, True)


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
  </IndexDocument>
  <ErrorDocument>
    <Key>{1}</Key>
  </ErrorDocument>
</WebsiteConfiguration>'''

        for index, error in [('index+中文.html', 'error.中文') ,(u'中-+()文.index', u'@#$%中文.error')]:
            req_info = mock_response(do_request, response_text.format(to_string(index), to_string(error)))

            result = bucket().get_bucket_website()

            self.assertRequest(req_info, request_text)
            self.assertEqual(result.error_file, to_string(error))


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
</WebsiteConfiguration>'''

        for index, error in [('index+中文.html', 'error.中文') ,(u'中-+()文.index', u'@#$%中文.error')]:
            req_info = mock_response(do_request, response_text.format(to_string(index), to_string(error)))

            result = bucket().get_bucket_website()

            self.assertRequest(req_info, request_text)
            self.assertEqual(result.index_file, to_string(index))


    @patch('oss2.Session.do_request')
    def test_put_bucket_requester_qos_info(self, do_request):
        request_text = '''PUT /?requesterQosInfo&qosRequester=uid-test HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<QoSConfiguration>
<TotalUploadBandwidth>10</TotalUploadBandwidth>
<IntranetUploadBandwidth>-1</IntranetUploadBandwidth>
<ExtranetUploadBandwidth>-2</ExtranetUploadBandwidth>
<TotalDownloadBandwidth>11</TotalDownloadBandwidth>
<IntranetDownloadBandwidth>-4</IntranetDownloadBandwidth>
<ExtranetDownloadBandwidth>-5</ExtranetDownloadBandwidth>
<TotalQps>1000</TotalQps>
<IntranetQps>-6</IntranetQps>
<ExtranetQps>-7</ExtranetQps>
</QoSConfiguration>
'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)
        uid = 'uid-test'
        qos_info = QoSConfiguration(
            total_upload_bw = 10,
            intranet_upload_bw = -1,
            extranet_upload_bw = -2,
            total_download_bw = 11,
            intranet_download_bw = -4,
            extranet_download_bw = -5,
            total_qps = 1000,
            intranet_qps = -6,
            extranet_qps = -7)
        bucket().put_bucket_requester_qos_info(uid, qos_info)
        self.assertRequest(req_info, request_text.format(to_string(qos_info)))

    @patch('oss2.Session.do_request')
    def test_get_bucket_requester_qos_info(self, do_request):
        request_text = '''GET /?requesterQosInfo&qosRequester=21234567890123 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<RequesterQoSInfo>
  <Requester>21234567890123</Requester>
  <QoSConfiguration>
    <TotalUploadBandwidth>10</TotalUploadBandwidth>
    <IntranetUploadBandwidth>-1</IntranetUploadBandwidth>
    <ExtranetUploadBandwidth>-2</ExtranetUploadBandwidth>
    <TotalDownloadBandwidth>11</TotalDownloadBandwidth>
    <IntranetDownloadBandwidth>-3</IntranetDownloadBandwidth>
    <ExtranetDownloadBandwidth>-4</ExtranetDownloadBandwidth>
    <TotalQps>1000</TotalQps>
    <IntranetQps>-5</IntranetQps>
    <ExtranetQps>-6</ExtranetQps>
  </QoSConfiguration>
</RequesterQoSInfo>
'''

        req_info = mock_response(do_request, response_text)

        result = bucket().get_bucket_requester_qos_info('21234567890123')

        self.assertRequest(req_info, request_text)
        self.assertEqual('566B6BD927A4046E9C725578', result.request_id)
        self.assertEqual(200, result.status, )
        self.assertEqual('21234567890123', result.requester)
        self.assertEqual(10, result.qos_configuration.total_upload_bw)
        self.assertEqual(-1, result.qos_configuration.intranet_upload_bw)
        self.assertEqual(-2, result.qos_configuration.extranet_upload_bw)
        self.assertEqual(11, result.qos_configuration.total_download_bw)
        self.assertEqual(-3, result.qos_configuration.intranet_download_bw)
        self.assertEqual(-4, result.qos_configuration.extranet_download_bw)
        self.assertEqual(1000, result.qos_configuration.total_qps)
        self.assertEqual(-5, result.qos_configuration.intranet_qps)
        self.assertEqual(-6, result.qos_configuration.extranet_qps)


    @patch('oss2.Session.do_request')
    def test_list_bucket_requester_qos_infos(self, do_request):
        request_text = '''GET /?requesterQosInfo&max-keys=10&continuation-token=abcd HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<ListBucketRequesterQoSInfosResult>
  <Bucket>BucketName</Bucket>
  <ContinuationToken>123456789</ContinuationToken>
  <NextContinuationToken>234567890</NextContinuationToken>
  <IsTruncated>true</IsTruncated>
  <RequesterQoSInfo>
    <Requester>133456789</Requester>
    <QoSConfiguration>
      <TotalUploadBandwidth>10</TotalUploadBandwidth>
      <IntranetUploadBandwidth>-1</IntranetUploadBandwidth>
      <ExtranetUploadBandwidth>-12</ExtranetUploadBandwidth>
      <TotalDownloadBandwidth>10</TotalDownloadBandwidth>
      <IntranetDownloadBandwidth>-13</IntranetDownloadBandwidth>
      <ExtranetDownloadBandwidth>-14</ExtranetDownloadBandwidth>
      <TotalQps>1000</TotalQps>
      <IntranetQps>-15</IntranetQps>
      <ExtranetQps>-16</ExtranetQps>
    </QoSConfiguration>
  </RequesterQoSInfo>
  <RequesterQoSInfo>
    <Requester>1335567892</Requester>
    <QoSConfiguration>
      <TotalUploadBandwidth>10</TotalUploadBandwidth>
      <IntranetUploadBandwidth>-1</IntranetUploadBandwidth>
      <ExtranetUploadBandwidth>-1</ExtranetUploadBandwidth>
      <TotalDownloadBandwidth>10</TotalDownloadBandwidth>
      <IntranetDownloadBandwidth>-1</IntranetDownloadBandwidth>
      <ExtranetDownloadBandwidth>-1</ExtranetDownloadBandwidth>
      <TotalQps>1000</TotalQps>
      <IntranetQps>-1</IntranetQps>
      <ExtranetQps>-1</ExtranetQps>
    </QoSConfiguration>
  </RequesterQoSInfo>
    <RequesterQoSInfo>
    <Requester>1335567893</Requester>
    <QoSConfiguration>
    </QoSConfiguration>
  </RequesterQoSInfo>
</ListBucketRequesterQoSInfosResult>
'''

        req_info = mock_response(do_request, response_text)

        result = bucket().list_bucket_requester_qos_infos(continuation_token='abcd', max_keys=10)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)

        self.assertEqual('BucketName', result.bucket)
        self.assertEqual('123456789', result.continuation_token)
        self.assertEqual('234567890', result.next_continuation_token)
        self.assertEqual(True, result.is_truncated)
        self.assertEqual('133456789', result.requester_qos_info[0].requester)
        self.assertEqual(10, result.requester_qos_info[0].qos_configuration.total_upload_bw)
        self.assertEqual(-1, result.requester_qos_info[0].qos_configuration.intranet_upload_bw)
        self.assertEqual(-12, result.requester_qos_info[0].qos_configuration.extranet_upload_bw)
        self.assertEqual(10, result.requester_qos_info[0].qos_configuration.total_download_bw)
        self.assertEqual(-13, result.requester_qos_info[0].qos_configuration.intranet_download_bw)
        self.assertEqual(-14, result.requester_qos_info[0].qos_configuration.extranet_download_bw)
        self.assertEqual(1000, result.requester_qos_info[0].qos_configuration.total_qps)
        self.assertEqual(-15, result.requester_qos_info[0].qos_configuration.intranet_qps)
        self.assertEqual(-16, result.requester_qos_info[0].qos_configuration.extranet_qps)
        self.assertEqual('1335567892', result.requester_qos_info[1].requester)
        self.assertEqual(10, result.requester_qos_info[1].qos_configuration.total_upload_bw)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.intranet_upload_bw)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.extranet_upload_bw)
        self.assertEqual(10, result.requester_qos_info[1].qos_configuration.total_download_bw)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.intranet_download_bw)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.extranet_download_bw)
        self.assertEqual(1000, result.requester_qos_info[1].qos_configuration.total_qps)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.intranet_qps)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.extranet_qps)
        self.assertEqual('1335567893', result.requester_qos_info[2].requester)


    @patch('oss2.Session.do_request')
    def test_delete_bucket_requester_qos_info(self, do_request):
        request_text = '''DELETE /?requesterQosInfo&qosRequester=uid-test HTTP/1.1
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

        result = bucket().delete_bucket_requester_qos_info('uid-test')

        self.assertRequest(req_info, request_text)


    @patch('oss2.Session.do_request')
    def test_list_resource_pools(self, do_request):
        request_text = '''GET /?resourcePool&max-keys=10&continuation-token=abcd HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<ListResourcePoolsResult>
  <Region>oss-cn-shanghai</Region>
  <Owner>1032307xxxx72056</Owner>
  <ContinuationToken>abcd</ContinuationToken>
  <NextContinuationToken>xyz</NextContinuationToken>
  <IsTruncated>true</IsTruncated>
  <ResourcePool>
    <Name>resource-pool-for-ai</Name>
    <CreateTime>2024-07-24T08:42:32.000Z</CreateTime>
  </ResourcePool>
  <ResourcePool>
    <Name>resource-pool-for-video</Name>
    <CreateTime>2024-07-24T08:42:32.000Z</CreateTime>
  </ResourcePool>
  <ResourcePool>
  </ResourcePool>
</ListResourcePoolsResult>
'''

        req_info = mock_response(do_request, response_text)

        result = service().list_resource_pools(continuation_token='abcd', max_keys=10)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual('oss-cn-shanghai', result.region)
        self.assertEqual('1032307xxxx72056', result.owner)
        self.assertEqual('abcd', result.continuation_token)
        self.assertEqual('xyz', result.next_continuation_token)
        self.assertEqual(True, result.is_truncated)
        self.assertEqual('resource-pool-for-ai', result.resource_pool[0].name)
        self.assertEqual('2024-07-24T08:42:32.000Z', result.resource_pool[0].create_time)
        self.assertEqual('resource-pool-for-video', result.resource_pool[1].name)
        self.assertEqual('2024-07-24T08:42:32.000Z', result.resource_pool[1].create_time)


    @patch('oss2.Session.do_request')
    def test_get_resource_pool_info(self, do_request):
        request_text = '''GET /?resourcePoolInfo&resourcePool=resource-pool-for-ai HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<GetResourcePoolInfoResponse>
  <Region>oss-cn-shanghai</Region>
  <Name>resource-pool-for-ai</Name>
  <Owner>1032307xxxx72056</Owner>
  <CreateTime>2024-07-24T08:42:32.000Z</CreateTime>
  <QoSConfiguration>
      <TotalUploadBandwidth>200</TotalUploadBandwidth>
      <IntranetUploadBandwidth>16</IntranetUploadBandwidth>
      <ExtranetUploadBandwidth>112</ExtranetUploadBandwidth>
      <TotalDownloadBandwidth>210</TotalDownloadBandwidth>
      <IntranetDownloadBandwidth>120</IntranetDownloadBandwidth>
      <ExtranetDownloadBandwidth>150</ExtranetDownloadBandwidth>
      <TotalQps>400</TotalQps>
      <IntranetQps>260</IntranetQps>
      <ExtranetQps>270</ExtranetQps>
  </QoSConfiguration>
</GetResourcePoolInfoResponse>
'''

        req_info = mock_response(do_request, response_text)
        resource_pool_name = 'resource-pool-for-ai'
        result = service().get_resource_pool_info(resource_pool_name)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual('oss-cn-shanghai', result.region)
        self.assertEqual('1032307xxxx72056', result.owner)
        self.assertEqual('2024-07-24T08:42:32.000Z', result.create_time)
        self.assertEqual(200, result.qos_configuration.total_upload_bw)
        self.assertEqual(16, result.qos_configuration.intranet_upload_bw)
        self.assertEqual(112, result.qos_configuration.extranet_upload_bw)
        self.assertEqual(210, result.qos_configuration.total_download_bw)
        self.assertEqual(120, result.qos_configuration.intranet_download_bw)
        self.assertEqual(150, result.qos_configuration.extranet_download_bw)
        self.assertEqual(400, result.qos_configuration.total_qps)
        self.assertEqual(260, result.qos_configuration.intranet_qps)
        self.assertEqual(270, result.qos_configuration.extranet_qps)



    @patch('oss2.Session.do_request')
    def test_list_resource_pool_buckets(self, do_request):
        request_text = '''GET /?resourcePoolBuckets&resourcePool=resource-pool-for-ai&continuation-token=abcd&max-keys=2 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<ListResourcePoolBucketsResult>
  <ResourcePool>resource-pool-for-ai</ResourcePool>
  <ContinuationToken>abcd</ContinuationToken>
  <NextContinuationToken>defg</NextContinuationToken>
  <IsTruncated>false</IsTruncated>
  <ResourcePoolBucket>
    <Name>bucket-1</Name>
    <JoinTime>2024-07-24T08:42:32.000Z</JoinTime>
  </ResourcePoolBucket>
  <ResourcePoolBucket>
    <JoinTime>2024-05-24T08:42:33.000Z</JoinTime>
  </ResourcePoolBucket>
  <ResourcePoolBucket>
  </ResourcePoolBucket>
</ListResourcePoolBucketsResult>

'''

        req_info = mock_response(do_request, response_text)
        resource_pool_name = 'resource-pool-for-ai'
        result = service().list_resource_pool_buckets(resource_pool_name, continuation_token='abcd', max_keys=2)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(resource_pool_name, result.resource_pool)
        self.assertEqual('abcd', result.continuation_token)
        self.assertEqual('defg', result.next_continuation_token)
        self.assertEqual(False, result.is_truncated)
        self.assertEqual('bucket-1',result.resource_pool_buckets[0].name)
        self.assertEqual('2024-07-24T08:42:32.000Z',result.resource_pool_buckets[0].join_time)
        self.assertEqual('2024-05-24T08:42:33.000Z',result.resource_pool_buckets[1].join_time)


    @patch('oss2.Session.do_request')
    def test_put_resource_pool_requester_qos_info(self, do_request):
        request_text = '''PUT /?requesterQosInfo&resourcePool=resource-pool-for-ai&qosRequester=uid-test  HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****

<QoSConfiguration>
<TotalUploadBandwidth>10</TotalUploadBandwidth>
<IntranetUploadBandwidth>-1</IntranetUploadBandwidth>
<ExtranetUploadBandwidth>-2</ExtranetUploadBandwidth>
<TotalDownloadBandwidth>11</TotalDownloadBandwidth>
<IntranetDownloadBandwidth>-4</IntranetDownloadBandwidth>
<ExtranetDownloadBandwidth>-5</ExtranetDownloadBandwidth>
<TotalQps>1000</TotalQps>
<IntranetQps>-6</IntranetQps>
<ExtranetQps>-7</ExtranetQps>
</QoSConfiguration>
'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 5C1B138A109F4E405B2D
content-length: 0
x-oss-console-auth: success
server: AliyunOSS
x-oss-server-time: 980
connection: keep-alive
date: Wed, 15 Sep 2021 03:33:37 GMT'''

        req_info = mock_response(do_request, response_text)
        uid = 'uid-test'
        resource_pool_name = 'resource-pool-for-ai'
        qos_info = QoSConfiguration(
            total_upload_bw = 10,
            intranet_upload_bw = -1,
            extranet_upload_bw = -2,
            total_download_bw = 11,
            intranet_download_bw = -4,
            extranet_download_bw = -5,
            total_qps = 1000,
            intranet_qps = -6,
            extranet_qps = -7)
        service().put_resource_pool_requester_qos_info(uid, resource_pool_name, qos_info)
        self.assertRequest(req_info, request_text.format(to_string(qos_info)))


    @patch('oss2.Session.do_request')
    def test_get_resource_pool_requester_qos_info(self, do_request):
        request_text = '''GET /?requesterQosInfo&resourcePool=resource-pool-for-ai&qosRequester=20123345678903 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<RequesterQoSInfo>
  <Requester>20123345678903</Requester>
  <QoSConfiguration>
      <TotalUploadBandwidth>200</TotalUploadBandwidth>
      <IntranetUploadBandwidth>16</IntranetUploadBandwidth>
      <ExtranetUploadBandwidth>112</ExtranetUploadBandwidth>
      <TotalDownloadBandwidth>210</TotalDownloadBandwidth>
      <IntranetDownloadBandwidth>120</IntranetDownloadBandwidth>
      <ExtranetDownloadBandwidth>150</ExtranetDownloadBandwidth>
      <TotalQps>400</TotalQps>
      <IntranetQps>260</IntranetQps>
      <ExtranetQps>270</ExtranetQps>
  </QoSConfiguration>
</RequesterQoSInfo>
'''

        req_info = mock_response(do_request, response_text)
        uid = '20123345678903'
        resource_pool_name = 'resource-pool-for-ai'
        result = service().get_resource_pool_requester_qos_info(uid, resource_pool_name)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(200, result.qos_configuration.total_upload_bw)
        self.assertEqual(16, result.qos_configuration.intranet_upload_bw)
        self.assertEqual(112, result.qos_configuration.extranet_upload_bw)
        self.assertEqual(210, result.qos_configuration.total_download_bw)
        self.assertEqual(120, result.qos_configuration.intranet_download_bw)
        self.assertEqual(150, result.qos_configuration.extranet_download_bw)
        self.assertEqual(400, result.qos_configuration.total_qps)
        self.assertEqual(260, result.qos_configuration.intranet_qps)
        self.assertEqual(270, result.qos_configuration.extranet_qps)


    @patch('oss2.Session.do_request')
    def test_list_resource_pool_requester_qos_infos(self, do_request):
        request_text = '''GET /?requesterQosInfo&resourcePool=resource-pool-for-ai&continuation-token=1105678&max-keys=2 HTTP/1.1
Date: Fri , 30 Apr 2021 13:08:38 GMT
Content-Length：443
Host: oss-cn-hangzhou.aliyuncs.com
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6BD927A4046E9C725578
Date: Fri , 30 Apr 2021 13:08:38 GMT

<?xml version="1.0" encoding="UTF-8"?>
<ListResourcePoolRequesterQoSInfosResult>
  <ResourcePool>resource-pool-for-ai</ResourcePool>
  <ContinuationToken>1105678</ContinuationToken>
  <NextContinuationToken>3105678</NextContinuationToken>
  <IsTruncated>false</IsTruncated>
  <RequesterQoSInfo>
    <Requester>21234567890</Requester>
    <QoSConfiguration>
      <TotalUploadBandwidth>200</TotalUploadBandwidth>
      <IntranetUploadBandwidth>16</IntranetUploadBandwidth>
      <ExtranetUploadBandwidth>112</ExtranetUploadBandwidth>
      <TotalDownloadBandwidth>210</TotalDownloadBandwidth>
      <IntranetDownloadBandwidth>120</IntranetDownloadBandwidth>
      <ExtranetDownloadBandwidth>150</ExtranetDownloadBandwidth>
      <TotalQps>400</TotalQps>
      <IntranetQps>260</IntranetQps>
      <ExtranetQps>270</ExtranetQps>
    </QoSConfiguration>
  </RequesterQoSInfo>
  <RequesterQoSInfo>
    <Requester>21234667890</Requester>
    <QoSConfiguration>
      <TotalUploadBandwidth>10</TotalUploadBandwidth>
      <IntranetUploadBandwidth>-1</IntranetUploadBandwidth>
      <ExtranetUploadBandwidth>-1</ExtranetUploadBandwidth>
      <TotalDownloadBandwidth>10</TotalDownloadBandwidth>
      <IntranetDownloadBandwidth>-1</IntranetDownloadBandwidth>
      <ExtranetDownloadBandwidth>-1</ExtranetDownloadBandwidth>
      <TotalQps>1000</TotalQps>
      <IntranetQps>-1</IntranetQps>
      <ExtranetQps>-1</ExtranetQps>
    </QoSConfiguration>
  </RequesterQoSInfo>
  <RequesterQoSInfo>
    <Requester>21234667890</Requester>
    <QoSConfiguration>
    </QoSConfiguration>
  </RequesterQoSInfo>
</ListResourcePoolRequesterQoSInfosResult>

'''

        req_info = mock_response(do_request, response_text)

        resource_pool_name = 'resource-pool-for-ai'

        result = service().list_resource_pool_requester_qos_infos(resource_pool_name, continuation_token='1105678', max_keys=2)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BD927A4046E9C725578')
        self.assertEqual(result.status, 200)
        self.assertEqual(resource_pool_name, result.resource_pool)
        self.assertEqual('1105678', result.continuation_token)
        self.assertEqual('3105678', result.next_continuation_token)
        self.assertEqual(False, result.is_truncated)
        self.assertEqual('21234567890', result.requester_qos_info[0].requester)
        self.assertEqual(200, result.requester_qos_info[0].qos_configuration.total_upload_bw)
        self.assertEqual(16, result.requester_qos_info[0].qos_configuration.intranet_upload_bw)
        self.assertEqual(112, result.requester_qos_info[0].qos_configuration.extranet_upload_bw)
        self.assertEqual(210, result.requester_qos_info[0].qos_configuration.total_download_bw)
        self.assertEqual(120, result.requester_qos_info[0].qos_configuration.intranet_download_bw)
        self.assertEqual(150, result.requester_qos_info[0].qos_configuration.extranet_download_bw)
        self.assertEqual(400, result.requester_qos_info[0].qos_configuration.total_qps)
        self.assertEqual(260, result.requester_qos_info[0].qos_configuration.intranet_qps)
        self.assertEqual(270, result.requester_qos_info[0].qos_configuration.extranet_qps)
        self.assertEqual('21234667890', result.requester_qos_info[1].requester)
        self.assertEqual(10, result.requester_qos_info[1].qos_configuration.total_upload_bw)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.intranet_upload_bw)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.extranet_upload_bw)
        self.assertEqual(10, result.requester_qos_info[1].qos_configuration.total_download_bw)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.intranet_download_bw)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.extranet_download_bw)
        self.assertEqual(1000, result.requester_qos_info[1].qos_configuration.total_qps)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.intranet_qps)
        self.assertEqual(-1, result.requester_qos_info[1].qos_configuration.extranet_qps)
        self.assertEqual('21234667890', result.requester_qos_info[2].requester)


    @patch('oss2.Session.do_request')
    def test_delete_resource_pool_requester_qos_info(self, do_request):
        request_text = '''DELETE /?requesterQosInfo&resourcePool=resource-pool-for-ai&qosRequester=20123345678903 HTTP/1.1
Host: oss-cn-hangzhou.aliyuncs.com
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

        uid = '20123345678903'
        resource_pool_name = 'resource-pool-for-ai'
        result = service().delete_resource_pool_requester_qos_info(uid, resource_pool_name)

        self.assertRequest(req_info, request_text)


if __name__ == '__main__':
    unittest.main()
