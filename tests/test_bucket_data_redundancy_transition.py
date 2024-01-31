from .common import *

class TestBucketDataRedundancyTransition(OssTestCase):
    def test_bucket_data_redundancy_transition_normal(self):
        result = self.bucket.create_bucket_data_redundancy_transition('ZRS')
        self.assertEqual(200, result.status)

        get_result = self.bucket.get_bucket_data_redundancy_transition(result.task_id)
        self.assertEqual(200, get_result.status)
        self.assertIsNotNone(get_result.task_id)
        self.assertIsNotNone(get_result.transition_status)

        service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)
        list_user_result = service.list_user_data_redundancy_transition(continuation_token='', max_keys=10)
        self.assertEqual(200, list_user_result.status)
        self.assertEqual(self.OSS_BUCKET, list_user_result.data_redundancy_transitions[0].bucket)
        self.assertEqual(get_result.task_id, list_user_result.data_redundancy_transitions[0].task_id)
        self.assertEqual(get_result.create_time, list_user_result.data_redundancy_transitions[0].create_time)
        self.assertEqual(get_result.start_time, list_user_result.data_redundancy_transitions[0].start_time)
        self.assertEqual(get_result.end_time, list_user_result.data_redundancy_transitions[0].end_time)
        self.assertEqual(get_result.transition_status, list_user_result.data_redundancy_transitions[0].transition_status)
        self.assertEqual(get_result.estimated_remaining_time, list_user_result.data_redundancy_transitions[0].estimated_remaining_time)
        self.assertEqual(get_result.process_percentage, list_user_result.data_redundancy_transitions[0].process_percentage)

        list_bucket_result = self.bucket.list_bucket_data_redundancy_transition()
        self.assertEqual(200, list_bucket_result.status)
        self.assertEqual(self.OSS_BUCKET, list_bucket_result.data_redundancy_transitions[0].bucket)
        self.assertEqual(get_result.task_id, list_bucket_result.data_redundancy_transitions[0].task_id)
        self.assertEqual(get_result.create_time, list_bucket_result.data_redundancy_transitions[0].create_time)
        self.assertEqual(get_result.start_time, list_bucket_result.data_redundancy_transitions[0].start_time)
        self.assertEqual(get_result.end_time, list_bucket_result.data_redundancy_transitions[0].end_time)
        self.assertEqual(get_result.transition_status, list_bucket_result.data_redundancy_transitions[0].transition_status)
        self.assertEqual(get_result.estimated_remaining_time, list_bucket_result.data_redundancy_transitions[0].estimated_remaining_time)
        self.assertEqual(get_result.process_percentage, list_bucket_result.data_redundancy_transitions[0].process_percentage)

        del_result = self.bucket.delete_bucket_data_redundancy_transition(result.task_id)
        self.assertEqual(204, del_result.status)


if __name__ == '__main__':
    unittest.main()
