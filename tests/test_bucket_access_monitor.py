from .common import *

class TestBucketAccessMonitor(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)

    def tearDown(self):
        try:
            OssTestCase.tearDown(self)
        except:
            pass

    def test_access_monitor(self):
        self.bucket.put_bucket_access_monitor("Enabled")

        while True:
            time.sleep(5)
            get_result = self.bucket.get_bucket_access_monitor()
            if get_result.access_monitor.status == 'Enabled':
                break

        self.bucket.put_bucket_access_monitor("Disabled")

        while True:
            time.sleep(5)
            get_result = self.bucket.get_bucket_access_monitor()
            if get_result.access_monitor.status == 'Disabled':
                break

        try:
            self.bucket.put_bucket_access_monitor("aa")
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.details['Code'], 'MalformedXML')

    def test_access_monitor_with_get_bucket_info(self):
        result = self.bucket.get_bucket_info()
        self.assertEqual(result.name, self.bucket.bucket_name)
        self.assertEqual(result.access_monitor, "Disabled")

        self.bucket.put_bucket_access_monitor("Enabled")

        result = self.bucket.get_bucket_info()

        self.assertEqual(result.name, self.bucket.bucket_name)
        self.assertEqual(result.access_monitor, "Enabled")

    def test_access_monitor_with_bucket_lifecycle(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition
        from oss2.models import NoncurrentVersionStorageTransition, NoncurrentVersionExpiration

        self.bucket.put_bucket_access_monitor("Enabled")

        time.sleep(5)

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=356))
        rule.storage_transitions = [StorageTransition(days=355,
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_ARCHIVE, is_access_time=False),
                                    StorageTransition(days=352,
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA, is_access_time=True, return_to_std_when_visit=True, allow_small_file=True)]

        lifecycle = BucketLifecycle([rule])

        put_result = self.bucket.put_bucket_lifecycle(lifecycle)
        self.assertEqual(put_result.status, 200)

        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(2, len(result.rules[0].storage_transitions))
        self.assertEqual(355, result.rules[0].storage_transitions[0].days)
        self.assertEqual(False, result.rules[0].storage_transitions[0].is_access_time)
        self.assertEqual(352, result.rules[0].storage_transitions[1].days)
        self.assertEqual(True, result.rules[0].storage_transitions[1].is_access_time)
        self.assertEqual(True, result.rules[0].storage_transitions[1].return_to_std_when_visit)
        self.assertEqual(True, result.rules[0].storage_transitions[1].allow_small_file)


        rule = LifecycleRule('rule1', 'test-prefix',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(expired_detete_marker=True),
                             noncurrent_version_expiration = NoncurrentVersionExpiration(30),
                             noncurrent_version_sotrage_transitions =
                             [NoncurrentVersionStorageTransition(25, oss2.BUCKET_STORAGE_CLASS_ARCHIVE, is_access_time=False),
                              NoncurrentVersionStorageTransition(22, oss2.BUCKET_STORAGE_CLASS_IA, is_access_time=True, return_to_std_when_visit=False, allow_small_file=True)])

        lifecycle = BucketLifecycle([rule])

        put_result2 = self.bucket.put_bucket_lifecycle(lifecycle)

        self.assertEqual(put_result2.status, 200)

        result2 = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result2.rules))
        self.assertEqual(2, len(result2.rules[0].noncurrent_version_sotrage_transitions))
        self.assertEqual(30, result2.rules[0].noncurrent_version_expiration.noncurrent_days)
        self.assertEqual(False, result2.rules[0].noncurrent_version_sotrage_transitions[0].is_access_time)
        self.assertEqual(True, result2.rules[0].noncurrent_version_sotrage_transitions[1].is_access_time)
        self.assertEqual(False, result2.rules[0].noncurrent_version_sotrage_transitions[1].return_to_std_when_visit)
        self.assertEqual(True, result2.rules[0].noncurrent_version_sotrage_transitions[1].allow_small_file)

    def test_access_monitor_with_get_object_meta(self):
        key = 'a.txt'
        self.bucket.put_object(key, 'content')
        self.bucket.put_bucket_access_monitor("Enabled")

        result = self.bucket.get_object_meta(key)

        self.assertIsNotNone(result.headers['x-oss-last-access-time'])


if __name__ == '__main__':
    unittest.main()
