from .common import *

class TestBucketArchiveDirectRead(OssTestCase):
    def test_bucket_archive_direct_read(self):
        result = self.bucket.put_bucket_archive_direct_read(True)
        self.assertEqual(200, result.status)

        get_result = self.bucket.get_bucket_archive_direct_read()
        self.assertEqual(True, get_result.enabled)

        result2 = self.bucket.put_bucket_archive_direct_read()
        self.assertEqual(200, result2.status)

        get_result2 = self.bucket.get_bucket_archive_direct_read()
        self.assertEqual(False, get_result2.enabled)

        try:
            self.bucket.put_bucket_archive_direct_read("aa")
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.details['Code'], 'MalformedXML')



if __name__ == '__main__':
    unittest.main()
