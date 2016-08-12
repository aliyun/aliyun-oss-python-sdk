# -*- coding: utf-8 -*-

import requests

from common import *

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
        clt = client.AcsClient(access_key_id, access_key_secret, OSS_STS_REGION)
        req = AssumeRoleRequest.AssumeRoleRequest()

        req.set_accept_format('json')
        req.set_RoleArn(role_arn)
        req.set_RoleSessionName('oss-python-sdk-test')

        body = clt.do_action(req)

        j = json.loads(body)

        token = StsToken()

        token.access_key_id = j['Credentials']['AccessKeyId']
        token.access_key_secret = j['Credentials']['AccessKeySecret']
        token.security_token = j['Credentials']['SecurityToken']
        token.request_id = j['RequestId']
        token.expiration = oss2.utils.to_unixtime(j['Credentials']['Expiration'], '%Y-%m-%dT%H:%M:%SZ')

        return token


    class TestSts(unittest.TestCase):
        def setUp(self):
            self.bucket = None
            self.key_list = []
            self.prefix = 'sts-' + random_string(8) + '/'

        def tearDown(self):
            if self.bucket is not None:
                delete_keys(self.bucket, self.key_list)

        def random_key(self, suffix=''):
            key = self.prefix + random_string(12) + suffix
            self.key_list.append(key)

            return key

        def init_bucket(self):
            self.token = fetch_sts_token(OSS_STS_ID, OSS_STS_KEY, OSS_STS_ARN)

            auth = oss2.StsAuth(self.token.access_key_id, self.token.access_key_secret, self.token.security_token)
            self.bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET)

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
            url = self.bucket.sign_url('GET', key, 60)

            resp = requests.get(url)
            self.assertEqual(content, resp.content)

        def test_rtmp(self):
            channel_name = 'test-sign-rtmp-url'
            
            self.init_bucket()
            
            self.bucket.list_live_channel()
            
            url = self.bucket.sign_rtmp_url(channel_name, 'test.m3u8', 3600)
            self.assertTrue('security-token=' in url)
