# -*- coding: utf-8 -*-

import os
import random
import string
import unittest
import time
import tempfile
import errno
import logging

import oss2

logging.basicConfig(level=logging.DEBUG)

OSS_ID = os.getenv("OSS_TEST_ACCESS_KEY_ID")
OSS_SECRET = os.getenv("OSS_TEST_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_TEST_ENDPOINT")
OSS_TEST_BUCKET = os.getenv("OSS_TEST_BUCKET")
OSS_CNAME = os.getenv("OSS_TEST_CNAME")
OSS_CMK = os.getenv("OSS_TEST_CMK")
OSS_REGION = os.getenv("OSS_TEST_REGION", "cn-hangzhou")

OSS_STS_ID = os.getenv("OSS_TEST_STS_ID")
OSS_STS_KEY = os.getenv("OSS_TEST_STS_KEY")
OSS_STS_ARN = os.getenv("OSS_TEST_STS_ARN")

OSS_PAYER_UID = os.getenv("OSS_TEST_PAYER_UID")
OSS_PAYER_ID = os.getenv("OSS_TEST_PAYER_ACCESS_KEY_ID")
OSS_PAYER_SECRET = os.getenv("OSS_TEST_PAYER_ACCESS_KEY_SECRET")

OSS_AUTH_VERSION = None

def random_string(n):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(n))

OSS_BUCKET = ''
if OSS_TEST_BUCKET is None:
    OSS_BUCKET = 'oss-python-sdk-'+random_string(10)
else:
    OSS_BUCKET = OSS_TEST_BUCKET + random_string(10)

def random_bytes(n):
    return oss2.to_bytes(random_string(n))

def clean_and_delete_bucket(bucket):
    # check if bucket is in versioning status
    try:
        result = bucket.get_bucket_info()
        if result.versioning_status in [oss2.BUCKET_VERSIONING_ENABLE, oss2.BUCKET_VERSIONING_SUSPEND]:
            all_objects = bucket.list_object_versions()
            for obj in all_objects.versions:
                bucket.delete_object(obj.key, params={'versionId': obj.versionid})
    except:
        pass
    
    # list all upload_parts to delete
    up_iter = oss2.MultipartUploadIterator(bucket)
    for up in up_iter:
        bucket.abort_multipart_upload(up.key, up.upload_id)

    # list all objects to delete
    obj_iter = oss2.ObjectIterator(bucket)
    for obj in obj_iter:
        bucket.delete_object(obj.key)
    
    # list all live channels to delete
    for ch_iter in oss2.LiveChannelIterator(bucket):
        bucket.delete_live_channel(ch_iter.name)

    # delete_bucket
    bucket.delete_bucket()

def clean_and_delete_bucket_by_prefix(bucket_prefix):
    service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)
    buckets = service.list_buckets(prefix=bucket_prefix).buckets
    for b in buckets:
        bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), b.extranet_endpoint, b.name)
        clean_and_delete_bucket(bucket)
        

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
        time.sleep(5)
    else:
        time.sleep(1)


class OssTestCase(unittest.TestCase):
    SINGLE_THREAD_CASE = 'single thread case'

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

        global OSS_AUTH_VERSION
        OSS_AUTH_VERSION = os.getenv('OSS_TEST_AUTH_VERSION')
        
        self.bucket = oss2.Bucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), OSS_ENDPOINT, OSS_BUCKET)

        try:
            self.bucket.create_bucket()
        except:
            pass

        self.rsa_crypto_bucket = oss2.CryptoBucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), OSS_ENDPOINT, OSS_BUCKET,
                                             crypto_provider=oss2.LocalRsaProvider())

        self.kms_crypto_bucket = oss2.CryptoBucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), OSS_ENDPOINT, OSS_BUCKET,
                                             crypto_provider=oss2.AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK))

        self.key_list = []
        self.temp_files = []

    def tearDown(self):
        for temp_file in self.temp_files:
            oss2.utils.silently_remove(temp_file)

        clean_and_delete_bucket(self.bucket)
        clean_and_delete_bucket_by_prefix(OSS_BUCKET + "-test-")

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

