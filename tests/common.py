import os
import random
import string
import unittest
import time
import tempfile
import errno

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


class NonlocalObject(object):
    def __init__(self, value):
        self.var = value


def wait_meta_sync():
    if os.environ.get('TRAVIS'):
        time.sleep(15)
    else:
        time.sleep(1)


class OssTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(OssTestCase, self).__init__(*args, **kwargs)
        self.bucket = None
        self.prefix = random_string(12)
        self.default_connect_timeout = oss2.defaults.connect_timeout
        self.default_multipart_num_threads = oss2.defaults.multipart_threshold

        self.default_multiget_threshold = 1024 * 1024
        self.default_multiget_part_size = 100 * 1024

    def setUp(self):
        oss2.defaults.connect_timeout = self.default_connect_timeout
        oss2.defaults.multipart_threshold = self.default_multipart_num_threads
        oss2.defaults.multipart_num_threads = random.randint(1, 5)

        oss2.defaults.multiget_threshold = self.default_multiget_threshold
        oss2.defaults.multiget_part_size = self.default_multiget_part_size
        oss2.defaults.multiget_num_threads = random.randint(1, 5)

        self.bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)
        self.bucket.create_bucket()
        self.key_list = []
        self.temp_files = []

    def tearDown(self):
        for temp_file in self.temp_files:
            oss2.utils.silently_remove(temp_file)

        delete_keys(self.bucket, self.key_list)

    def random_key(self, suffix=''):
        key = self.prefix + random_string(12) + suffix
        self.key_list.append(key)

        return key

    def random_filename(self):
        filename = random_string(16)
        self.temp_files.append(filename)

        return filename

    def _prepare_temp_file(self, content):
        fd, pathname = tempfile.mkstemp(suffix='test-upload')

        os.write(fd, content)
        os.close(fd)

        self.temp_files.append(pathname)
        return pathname

    def _prepare_temp_file_with_size(self, size):
        fd, pathname = tempfile.mkstemp(suffix='test-upload')

        block_size = 8 * 1024 * 1024
        num_written = 0

        while num_written < size:
            to_write = min(block_size, size - num_written)
            num_written += to_write

            content = 's' * to_write
            os.write(fd, oss2.to_bytes(content))

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

    def assertFileContent(self, filename, content):
        with open(filename, 'rb') as f:
            read = f.read()
            self.assertEqual(len(read), len(content))
            self.assertEqual(read, content)

    def assertFileContentNotEqual(self, filename, content):
        with open(filename, 'rb') as f:
            read = f.read()
            self.assertNotEqual(len(read), len(content))
            self.assertNotEqual(read, content)
