from .common import *


class TestBucketTransferAccelerat(OssTestCase):
    def test_bucket_transfer_acceleration_normal(self):
        result = self.bucket.put_bucket_transfer_acceleration('true')
        self.assertEqual(200, result.status)

        get_result = self.bucket.get_bucket_transfer_acceleration()
        self.assertEqual('true', get_result.enabled)

    def test_bucket_worm_illegal(self):
        self.assertRaises(oss2.exceptions.NoSuchTransferAccelerationConfiguration, self.bucket.get_bucket_transfer_acceleration)


if __name__ == '__main__':
    unittest.main()
