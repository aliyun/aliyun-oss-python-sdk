# -*- coding: utf-8 -*-

import os
import oss2
from .common import *

class TestProxy(OssTestCase):
    def test_with_proxy(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-proxy"

        proxies = {'http': 'http://localhost:8888'}

        try:
            bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name, proxies=proxies)
            bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE, oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_ARCHIVE))
            self.assertTrue(False)
        except oss2.exceptions.RequestError as e:
            self.assertTrue(e.body.startswith("RequestError: HTTPConnectionPool(host='localhost', port=8888)"))
        except:
            self.assertTrue(False)


        try:
            service = oss2.Service(auth, OSS_ENDPOINT, proxies=proxies)
            service.list_buckets()
            self.assertTrue(False)
        except oss2.exceptions.RequestError as e:
            self.assertTrue(e.body.startswith("RequestError: HTTPConnectionPool(host='localhost', port=8888)"))
        except:
            self.assertTrue(False)


        bucket1 = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        bucket1.create_bucket()

        service1 = oss2.Service(auth, OSS_ENDPOINT)
        wait_meta_sync()
        self.retry_assert(lambda: bucket1.bucket_name in (b.name for b in
                                                         service1.list_buckets(prefix=bucket1.bucket_name).buckets))

if __name__ == '__main__':
    unittest.main()