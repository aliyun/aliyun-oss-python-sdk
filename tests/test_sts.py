# -*- coding: utf-8 -*-

import requests

from .common import *

if oss2.compat.is_py2:
    from aliyunsdkcore import client
    from aliyunsdksts.request.v20150401 import AssumeRoleRequest

    import json


    class StsToken(object):
        def __init__(self):
            self.access_key_id = ''
            self.access_key_secret = ''
            self.expiration = 0
            self.security_token = ''
            self.request_id = ''


    def fetch_sts_token(access_key_id, access_key_secret, role_arn):
        clt = client.AcsClient(access_key_id, access_key_secret, OSS_REGION)
        req = AssumeRoleRequest.AssumeRoleRequest()

        req.set_accept_format('json')
        req.set_RoleArn(role_arn)
        req.set_RoleSessionName('oss-python-sdk-test')

        body = clt.do_action_with_exception(req)

        j = json.loads(oss2.to_unicode(body))

        token = StsToken()

        token.access_key_id = j['Credentials']['AccessKeyId']
        token.access_key_secret = j['Credentials']['AccessKeySecret']
        token.security_token = j['Credentials']['SecurityToken']
        token.request_id = j['RequestId']
        token.expiration = oss2.utils.to_unixtime(j['Credentials']['Expiration'], '%Y-%m-%dT%H:%M:%SZ')

        return token


    class TestSTSAuth(oss2.StsAuth):
        def __init__(self, access_key_id, access_key_secret, security_token):
            super(TestSTSAuth, self).__init__(access_key_id,
                                              access_key_secret,
                                              security_token,
                                              os.getenv('OSS_TEST_AUTH_VERSION'))

    oss2.StsAuth = TestSTSAuth

    class TestSts(unittest.TestCase):
        def setUp(self):
            self.bucket = None
            self.key_list = []
            self.prefix = 'sts-' + random_string(8) + '/'

        def tearDown(self):
            if self.bucket is not None:
                clean_and_delete_bucket(self.bucket)

        def random_key(self, suffix=''):
            key = self.prefix + random_string(12) + suffix
            self.key_list.append(key)

            return key

        def init_bucket(self):
            self.token = fetch_sts_token(OSS_STS_ID, OSS_STS_KEY, OSS_STS_ARN)

            auth = oss2.StsAuth(self.token.access_key_id, self.token.access_key_secret, self.token.security_token)
            self.bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET)
            self.bucket.create_bucket()

        def test_object(self):
            self.init_bucket()

            key = self.random_key()
            content = b'hello world'

            self.bucket.put_object(key, content)
            self.assertEqual(self.bucket.get_object(key).read(), content)

            self.bucket.delete_object(key)

        def test_bucket(self):
            self.init_bucket()

            # just make sure no exception being thrown
            self.bucket.get_bucket_referer()

        def test_url(self):
            self.init_bucket()

            key = self.random_key()
            content = b'Ali Baba'

            self.bucket.put_object(key, content)
            url = self.bucket.sign_url('GET', key, 60, params={'para1':'test'})

            resp = requests.get(url)
            self.assertEqual(content, resp.content)

        def test_rtmp(self):
            channel_name = 'test-sign-rtmp-url'
            
            self.init_bucket()
            
            self.bucket.list_live_channel()
            
            url = self.bucket.sign_rtmp_url(channel_name, 'test.m3u8', 3600)
            self.assertTrue('security-token=' in url)

    class TestSign(TestSts):
        """
            这个类主要是用来增加测试覆盖率，当环境变量为oss2.AUTH_VERSION_2，则重新设置为oss2.AUTH_VERSION_1再运行TestSts，反之亦然
        """
        def __init__(self, *args, **kwargs):
            super(TestSign, self).__init__(*args, **kwargs)

        def setUp(self):
            if os.getenv('OSS_TEST_AUTH_VERSION') == oss2.AUTH_VERSION_2:
                os.environ['OSS_TEST_AUTH_VERSION'] = oss2.AUTH_VERSION_1
            else:
                os.environ['OSS_TEST_AUTH_VERSION'] = oss2.AUTH_VERSION_2
            super(TestSign, self).setUp()

        def tearDown(self):
            if os.getenv('OSS_TEST_AUTH_VERSION') == oss2.AUTH_VERSION_2:
                os.environ['OSS_TEST_AUTH_VERSION'] = oss2.AUTH_VERSION_1
            else:
                os.environ['OSS_TEST_AUTH_VERSION'] = oss2.AUTH_VERSION_2
            super(TestSign, self).tearDown()