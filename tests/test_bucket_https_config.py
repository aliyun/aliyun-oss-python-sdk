from oss2.models import BucketTlsVersion
from .common import *

class TestHttpsConfig(OssTestCase):
    def test_https_config_normal(self):
        https_config = BucketTlsVersion(True, ['TLSv1.2', 'TLSv1.3'])
        result = self.bucket.put_bucket_https_config(https_config)
        self.assertEqual(200, result.status)

        result2 = self.bucket.get_bucket_https_config()
        self.assertEqual(200, result2.status)
        self.assertEqual(result2.tls_enabled, True)
        self.assertListEqual(result2.tls_version, ['TLSv1.2', 'TLSv1.3'])

        https_config2 = BucketTlsVersion()
        result3 = self.bucket.put_bucket_https_config(https_config2)
        self.assertEqual(200, result3.status)

        result4 = self.bucket.get_bucket_https_config()
        self.assertEqual(200, result4.status)
        self.assertEqual(result4.tls_enabled, False)
        self.assertListEqual(result4.tls_version, [])


    def test_https_config_exception_1(self):
        try:
            https_config = BucketTlsVersion(True)
            self.bucket.put_bucket_https_config(https_config)
            self.assertTrue(False)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.code, 'MalformedXML')

    def test_https_config_exception_2(self):
        try:
            https_config = BucketTlsVersion(True, ['aaa', 'bbb'])
            self.bucket.put_bucket_https_config(https_config)
            self.assertTrue(False)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.code, 'MalformedXML')

    def test_https_config_exception_3(self):
        https_config = BucketTlsVersion(True, ['TLSv1.2', 'TLSv1.2'])
        result = self.bucket.put_bucket_https_config(https_config)
        self.assertEqual(200, result.status)

        result2 = self.bucket.get_bucket_https_config()
        self.assertEqual(200, result2.status)
        self.assertEqual(result2.tls_enabled, True)
        self.assertListEqual(result2.tls_version, ['TLSv1.2'])

if __name__ == '__main__':
    unittest.main()
