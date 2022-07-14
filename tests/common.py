# -*- coding: utf-8 -*-

import os
import random
import string
import unittest
import time
import tempfile
import errno
import logging
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
import oss2

logging.basicConfig(level=logging.DEBUG)

OSS_ID = os.getenv("OSS_TEST_ACCESS_KEY_ID")
OSS_SECRET = os.getenv("OSS_TEST_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_TEST_ENDPOINT")
OSS_TEST_BUCKET = os.getenv("OSS_TEST_BUCKET")
OSS_CNAME = os.getenv("OSS_TEST_CNAME")
OSS_REGION = os.getenv("OSS_TEST_REGION", "cn-hangzhou")

OSS_CMK = os.getenv("OSS_TEST_KMS_CMK_ID")
OSS_CMK_REGION = os.getenv("OSS_TEST_KMS_REGION")

OSS_STS_ID = os.getenv("OSS_TEST_STS_ID")
OSS_STS_KEY = os.getenv("OSS_TEST_STS_KEY")
OSS_STS_ARN = os.getenv("OSS_TEST_STS_ARN")

OSS_PAYER_UID = os.getenv("OSS_TEST_PAYER_UID")
OSS_PAYER_ID = os.getenv("OSS_TEST_PAYER_ACCESS_KEY_ID")
OSS_PAYER_SECRET = os.getenv("OSS_TEST_PAYER_ACCESS_KEY_SECRET")

OSS_INVENTORY_BUCKET_DESTINATION_ARN = os.getenv("OSS_TEST_RAM_ROLE_ARN")
OSS_INVENTORY_BUCKET_DESTINATION_ACCOUNT = os.getenv("OSS_TEST_RAM_UID")

OSS_AUTH_VERSION = None
OSS_TEST_AUTH_SERVER_HOST = os.getenv("OSS_TEST_AUTH_SERVER_HOST")

private_key = RSA.generate(1024)
public_key = private_key.publickey()
private_key_str = RsaKey.exportKey(private_key)
public_key_str = RsaKey.exportKey(public_key)
key_pair = {'private_key': private_key_str, 'public_key': public_key_str}

private_key_compact = '''-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgQCokfiAVXXf5ImFzKDw+XO/UByW6mse2QsIgz3ZwBtMNu59fR5z
ttSx+8fB7vR4CN3bTztrP9A6bjoN0FFnhlQ3vNJC5MFO1PByrE/MNd5AAfSVba93
I6sx8NSk5MzUCA4NJzAUqYOEWGtGBcom6kEF6MmR1EKib1Id8hpooY5xaQIDAQAB
AoGAOPUZgkNeEMinrw31U3b2JS5sepG6oDG2CKpPu8OtdZMaAkzEfVTJiVoJpP2Y
nPZiADhFW3e0ZAnak9BPsSsySRaSNmR465cG9tbqpXFKh9Rp/sCPo4Jq2n65yood
JBrnGr6/xhYvNa14sQ6xjjfSgRNBSXD1XXNF4kALwgZyCAECQQDV7t4bTx9FbEs5
36nAxPsPM6aACXaOkv6d9LXI7A0J8Zf42FeBV6RK0q7QG5iNNd1WJHSXIITUizVF
6aX5NnvFAkEAybeXNOwUvYtkgxF4s28s6gn11c5HZw4/a8vZm2tXXK/QfTQrJVXp
VwxmSr0FAajWAlcYN/fGkX1pWA041CKFVQJAG08ozzekeEpAuByTIOaEXgZr5MBQ
gBbHpgZNBl8Lsw9CJSQI15wGfv6yDiLXsH8FyC9TKs+d5Tv4Cvquk0efOQJAd9OC
lCKFs48hdyaiz9yEDsc57PdrvRFepVdj/gpGzD14mVerJbOiOF6aSV19ot27u4on
Td/3aifYs0CveHzFPQJAWb4LCDwqLctfzziG7/S7Z74gyq5qZF4FUElOAZkz718E
yZvADwuz/4aK0od0lX9c4Jp7Mo5vQ4TvdoBnPuGoyw==
-----END RSA PRIVATE KEY-----'''

public_key_compact = '''-----BEGIN RSA PUBLIC KEY-----
MIGJAoGBAKiR+IBVdd/kiYXMoPD5c79QHJbqax7ZCwiDPdnAG0w27n19HnO21LH7
x8Hu9HgI3dtPO2s/0DpuOg3QUWeGVDe80kLkwU7U8HKsT8w13kAB9JVtr3cjqzHw
1KTkzNQIDg0nMBSpg4RYa0YFyibqQQXoyZHUQqJvUh3yGmihjnFpAgMBAAE=
-----END RSA PUBLIC KEY-----'''

key_pair_compact = {'private_key': private_key_compact, 'public_key': public_key_compact}


def random_string(n):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(n))

OSS_BUCKET_BASE = ''
if OSS_TEST_BUCKET is None:
    OSS_BUCKET_BASE = 'oss-python-sdk-'+random_string(6)
else:
    OSS_BUCKET_BASE = OSS_TEST_BUCKET + random_string(6)

def random_bytes(n):
    return oss2.to_bytes(random_string(n))

def clean_and_delete_bucket(bucket):
    # check if bucket is in versioning status
    try:
        result = bucket.get_bucket_info()
        if result.versioning_status in [oss2.BUCKET_VERSIONING_ENABLE, oss2.BUCKET_VERSIONING_SUSPEND]:
            next_key_marker = None
            next_versionid_marker = None
            is_truncated = True
            while is_truncated is True:
                objects = bucket.list_object_versions(key_marker=next_key_marker, versionid_marker=next_versionid_marker)
                for obj in objects.versions:
                    bucket.delete_object(obj.key, params={'versionId': obj.versionid})
                for del_marker in objects.delete_marker:
                    bucket.delete_object(del_marker.key, params={'versionId': del_marker.versionid})
                is_truncated = objects.is_truncated
                if is_truncated:
                    next_key_marker = objects.next_key_marker
                    next_versionid_marker = objects.next_versionid_marker
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

        self.OSS_BUCKET = OSS_BUCKET_BASE + random_string(4)
        self.bucket = oss2.Bucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), OSS_ENDPOINT, self.OSS_BUCKET)

        try:
            self.bucket.create_bucket()
        except:
            pass

        self.rsa_crypto_bucket = oss2.CryptoBucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), OSS_ENDPOINT,
                                                   self.OSS_BUCKET, crypto_provider=oss2.RsaProvider(key_pair))

        self.kms_crypto_bucket = oss2.CryptoBucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), OSS_ENDPOINT,
                                                   self.OSS_BUCKET, crypto_provider=oss2.AliKMSProvider(OSS_ID, OSS_SECRET,
                                                                                                   OSS_REGION, OSS_CMK))

        self.key_list = []
        self.temp_files = []

    def tearDown(self):
        for temp_file in self.temp_files:
            oss2.utils.silently_remove(temp_file)

        clean_and_delete_bucket(self.bucket)
        clean_and_delete_bucket_by_prefix(self.OSS_BUCKET + "-test-")

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

