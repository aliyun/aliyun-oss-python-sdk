import os
import random
import string
import unittest
import time
import tempfile

import oss2


OSS_ID = os.getenv("OSS_TEST_ACCESS_KEY_ID")
OSS_SECRET = os.getenv("OSS_TEST_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_TEST_ENDPOINT")
OSS_BUCKET = os.getenv("OSS_TEST_BUCKET")
OSS_CNAME = os.getenv("OSS_TEST_CNAME")

OSS_STS_ID = os.getenv("OSS_TEST_STS_ID")
OSS_STS_KEY = os.getenv("OSS_TEST_STS_KEY")
OSS_STS_ARN = os.getenv("OSS_TEST_STS_ARN")
OSS_STS_REGION = os.getenv("OSS_TEST_STS_REGION", "cn-hangzhou")


def random_string(n):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(n))


def random_bytes(n):
    return oss2.to_bytes(random_string(n))


def delete_keys(bucket, key_list):
    if not key_list:
        return

    n = 100
    grouped = [key_list[i:i+n] for i in range(0, len(key_list), n)]
    for g in grouped:
        bucket.batch_delete_objects(g)


def wait_meta_sync():
    if os.environ.get('TRAVIS'):
        time.sleep(15)


class OssTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(OssTestCase, self).__init__(*args, **kwargs)
        self.bucket = None
        self.prefix = random_string(12)
        self.default_connect_timeout = oss2.defaults.connect_timeout

    def setUp(self):
        oss2.defaults.connect_timeout = self.default_connect_timeout

        self.bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)
        self.bucket.create_bucket()
        self.key_list = []
        self.temp_files = []

    def tearDown(self):
        for temp_file in self.temp_files:
            os.remove(temp_file)
        delete_keys(self.bucket, self.key_list)

    def random_key(self, suffix=''):
        key = self.prefix + random_string(12) + suffix
        self.key_list.append(key)

        return key

    def _prepare_temp_file(self, content):
        fd, pathname = tempfile.mkstemp(suffix='test-upload')

        os.write(fd, content)
        os.close(fd)

        self.temp_files.append(pathname)
        return pathname

    def retry_assert(self, func):
        for i in range(5):
            if func():
                return
            else:
                time.sleep(i+2)

        self.assertTrue(False)
