# -*- coding: utf-8 -*-

import os
import oss2
from .common import *
from oss2.models import ReplicationRule


class TestBucketReplication(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)
        source_bucket_name = self.OSS_BUCKET + '-test-replica-source-' + random_string(10)
        self.source_bucket = oss2.Bucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), OSS_ENDPOINT, source_bucket_name)
        self.source_bucket.create_bucket()

        self.replica_endpoint = "oss-ap-south-1"
        self.transfer_type = 'oss_acc'
        self.replica_bucket_name = self.OSS_BUCKET + "-test-replica-dest-" + random_string(10)
        self.replica_bucket = oss2.Bucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), self.replica_endpoint + '.aliyuncs.com', self.replica_bucket_name)
        self.replica_bucket.create_bucket()

        import time
        time.sleep(3)

        index = OSS_INVENTORY_BUCKET_DESTINATION_ARN.rfind('/')
        self.sync_role_name = OSS_INVENTORY_BUCKET_DESTINATION_ARN[index+1:] if index != -1 else OSS_INVENTORY_BUCKET_DESTINATION_ARN

    def test_replication_with_full_parameter(self):
        rule_id = 'test-id'
        prefix_list = ['prefix-1', 'prefix-2']
        replica_config = ReplicationRule(rule_id=rule_id,
                                         prefix_list=prefix_list,
                                         action_list=[ReplicationRule.ALL],
                                         target_bucket_name=self.replica_bucket_name,
                                         target_bucket_location=self.replica_endpoint,
                                         target_transfer_type=self.transfer_type,
                                         is_enable_historical_object_replication=False,
                                         sync_role_name=self.sync_role_name,
                                         replica_kms_keyid=OSS_CMK,
                                         sse_kms_encrypted_objects_status=ReplicationRule.ENABLED)
        result = self.source_bucket.put_bucket_replication(replica_config)
        self.assertEqual(200, result.status)

        result = self.source_bucket.get_bucket_replication()
        self.assertEqual(1, len(result.rule_list))
        rule = result.rule_list[0]
        self.assertEqual(rule_id, rule.rule_id)
        self.assertEqual(self.replica_bucket_name, rule.target_bucket_name)
        self.assertEqual(self.replica_endpoint, rule.target_bucket_location)
        self.assertEqual(self.transfer_type, rule.target_transfer_type)
        self.assertEqual(2, len(rule.prefix_list))
        self.assertTrue('prefix-1' in rule.prefix_list)
        self.assertTrue('prefix-2' in rule.prefix_list)
        self.assertEqual(1, len(rule.action_list))
        self.assertEqual(ReplicationRule.ALL, rule.action_list[0])
        self.assertFalse(rule.is_enable_historical_object_replication)
        self.assertEqual(ReplicationRule.STARTING, rule.status)
        self.assertEqual(self.sync_role_name, rule.sync_role_name)
        self.assertEqual(OSS_CMK, rule.replica_kms_keyid)
        self.assertEqual(ReplicationRule.ENABLED, rule.sse_kms_encrypted_objects_status)

        result = self.source_bucket.get_bucket_replication_progress(rule_id)
        progress = result.progress
        self.assertEqual(self.replica_bucket_name, progress.target_bucket_name)
        self.assertEqual(self.replica_endpoint, progress.target_bucket_location)
        self.assertEqual(rule_id, progress.rule_id)
        self.assertEqual(self.transfer_type, progress.target_transfer_type)
        self.assertEqual(2, len(rule.prefix_list))
        self.assertTrue('prefix-1' in rule.prefix_list)
        self.assertTrue('prefix-2' in rule.prefix_list)
        self.assertEqual(1, len(progress.action_list))
        self.assertEqual(ReplicationRule.ALL, progress.action_list[0])
        self.assertFalse(progress.is_enable_historical_object_replication)
        self.assertEqual(ReplicationRule.STARTING, progress.status)

        self.assertEqual(0, progress.historical_object_progress)
        self.assertIsNone(progress.new_object_progress)

        result = self.source_bucket.delete_bucket_replication(rule_id)
        self.assertEqual(200, result.status)

        result = self.source_bucket.get_bucket_replication()
        self.assertEqual(ReplicationRule.CLOSING, result.rule_list[0].status)

        result = self.source_bucket.get_bucket_replication_progress(rule_id)
        self.assertEqual(ReplicationRule.CLOSING, result.progress.status)

    def test_get_replication_location(self):
        result = self.source_bucket.get_bucket_replication_location()
        self.assertTrue(len(result.location_list) > 0)
        self.assertTrue(len(result.location_transfer_type_list) > 0)
        for location in result.location_list:
            self.assertIsNotNone(location)
        for location_transfer_type in result.location_transfer_type_list:
            self.assertIsNotNone(location_transfer_type.location)
            self.assertIsNotNone(location_transfer_type.transfer_type)

    def test_put_without_rule_id(self):
        prefix_list = ['prefix-1', 'prefix-2']
        replica_config = ReplicationRule(prefix_list=prefix_list,
                                         target_bucket_name=self.replica_bucket_name,
                                         target_bucket_location=self.replica_endpoint,
                                         target_transfer_type=self.transfer_type,
                                         sync_role_name=self.sync_role_name,
                                         replica_kms_keyid=OSS_CMK,
                                         sse_kms_encrypted_objects_status='Enabled')
        result = self.source_bucket.put_bucket_replication(replica_config)
        self.assertEqual(200, result.status)

        result = self.source_bucket.get_bucket_replication()
        self.assertEqual(1, len(result.rule_list))
        rule = result.rule_list[0]
        self.assertIsNotNone(rule.rule_id)
        self.assertEqual(self.replica_bucket_name, rule.target_bucket_name)
        self.assertEqual(self.replica_endpoint, rule.target_bucket_location)
        self.assertEqual(self.transfer_type, rule.target_transfer_type)
        self.assertEqual(2, len(rule.prefix_list))
        self.assertTrue('prefix-1' in rule.prefix_list)
        self.assertTrue('prefix-2' in rule.prefix_list)
        self.assertEqual(1, len(rule.action_list))
        self.assertEqual(ReplicationRule.ALL, rule.action_list[0])
        self.assertTrue(rule.is_enable_historical_object_replication)
        self.assertEqual(ReplicationRule.STARTING, rule.status)
        self.assertEqual(self.sync_role_name, rule.sync_role_name)
        self.assertEqual(OSS_CMK, rule.replica_kms_keyid)
        self.assertEqual('Enabled', rule.sse_kms_encrypted_objects_status)
        rule_id = rule.rule_id

        result = self.source_bucket.delete_bucket_replication(rule_id)
        self.assertEqual(200, result.status)

    def test_put_replica_without_prefix(self):
        rule_id = 'test-id'
        replica_config = ReplicationRule(rule_id=rule_id,
                                         target_bucket_name=self.replica_bucket_name,
                                         target_bucket_location=self.replica_endpoint,
                                         target_transfer_type=self.transfer_type,
                                         sync_role_name=self.sync_role_name,
                                         replica_kms_keyid=OSS_CMK,
                                         sse_kms_encrypted_objects_status='Enabled')
        result = self.source_bucket.put_bucket_replication(replica_config)
        self.assertEqual(200, result.status)

        result = self.source_bucket.get_bucket_replication()
        self.assertEqual(1, len(result.rule_list))
        rule = result.rule_list[0]
        self.assertIsInstance(rule.prefix_list, list)
        self.assertEqual(0, len(rule.prefix_list))

        result = self.source_bucket.get_bucket_replication_progress(rule_id)
        progress = result.progress
        self.assertEqual(0, len(progress.prefix_list))

        result = self.source_bucket.delete_bucket_replication(rule_id)
        self.assertEqual(200, result.status)

    def test_put_replica_without_sync_role(self):
        rule_id = 'test-id'
        prefix_list = ['prefix-1', 'prefix-2']
        replica_config = ReplicationRule(rule_id=rule_id,
                                         prefix_list=prefix_list,
                                         target_bucket_name=self.replica_bucket_name,
                                         target_bucket_location=self.replica_endpoint,
                                         target_transfer_type=self.transfer_type,
                                         replica_kms_keyid=OSS_CMK,
                                         sse_kms_encrypted_objects_status='Enabled')
        result = self.source_bucket.put_bucket_replication(replica_config)
        self.assertEqual(200, result.status)

        result = self.source_bucket.get_bucket_replication()
        self.assertEqual(1, len(result.rule_list))
        rule = result.rule_list[0]
        self.assertEqual(rule_id, rule.rule_id)
        self.assertIsNone(rule.sync_role_name)
        self.assertIsNone(rule.replica_kms_keyid)
        self.assertIsNone(rule.sse_kms_encrypted_objects_status)

        result = self.source_bucket.delete_bucket_replication(rule_id)
        self.assertEqual(200, result.status)

    def test_put_replica_without_action(self):
        rule_id = 'test-id'
        replica_config = ReplicationRule(rule_id=rule_id,
                                         target_bucket_name=self.replica_bucket_name,
                                         target_bucket_location=self.replica_endpoint,
                                         is_enable_historical_object_replication=True)
        self.source_bucket.put_bucket_replication(replica_config)

        result = self.source_bucket.get_bucket_replication()
        self.assertEqual(1, len(result.rule_list))
        rule = result.rule_list[0]
        self.assertTrue(rule.is_enable_historical_object_replication)
        self.assertEqual(ReplicationRule.ALL, rule.action_list[0])

    def test_put_replica_with_multi_action(self):
        rule_id = 'test-id'
        action_list = [ReplicationRule.PUT, ReplicationRule.DELETE, ReplicationRule.ABORT]
        replica_config = ReplicationRule(rule_id=rule_id,
                                         target_bucket_name=self.replica_bucket_name,
                                         target_bucket_location=self.replica_endpoint,
                                         action_list=action_list)
        self.source_bucket.put_bucket_replication(replica_config)

        result = self.source_bucket.get_bucket_replication()
        self.assertEqual(1, len(result.rule_list))
        rule = result.rule_list[0]
        self.assertEqual(3, len(rule.action_list))
        self.assertTrue('PUT' in rule.action_list)
        self.assertTrue('DELETE' in rule.action_list)
        self.assertTrue('ABORT' in rule.action_list)

    def test_put_multi_replica_rule(self):

        rule_id = 'test-id'
        action_list = [ReplicationRule.PUT, ReplicationRule.DELETE, ReplicationRule.ABORT]
        replica_config = ReplicationRule(rule_id=rule_id,
                                         target_bucket_name=self.replica_bucket_name,
                                         target_bucket_location=self.replica_endpoint,
                                         action_list=action_list)
        self.source_bucket.put_bucket_replication(replica_config)

        rule_id_2 = 'test-id-2'
        action_list = [ReplicationRule.PUT, ReplicationRule.DELETE, ReplicationRule.ABORT]
        replica_config = ReplicationRule(rule_id=rule_id_2,
                                         target_bucket_name=self.replica_bucket_name,
                                         target_bucket_location=self.replica_endpoint,
                                         action_list=action_list)
        self.assertRaises(oss2.exceptions.BucketReplicationAlreadyExist, self.source_bucket.put_bucket_replication, replica_config)

    def test_kms_encrypted_status_disabled(self):
        rule_id = 'test-id'
        prefix_list = ['prefix-1', 'prefix-2']
        replica_config = ReplicationRule(rule_id=rule_id,
                                         prefix_list=prefix_list,
                                         target_bucket_name=self.replica_bucket_name,
                                         target_bucket_location=self.replica_endpoint,
                                         target_transfer_type=self.transfer_type,
                                         sync_role_name=self.sync_role_name,
                                         replica_kms_keyid=OSS_CMK,
                                         sse_kms_encrypted_objects_status=ReplicationRule.DISABLED)
        result = self.source_bucket.put_bucket_replication(replica_config)
        self.assertEqual(200, result.status)

        result = self.source_bucket.get_bucket_replication()
        self.assertEqual(1, len(result.rule_list))
        rule = result.rule_list[0]
        self.assertEqual(rule_id, rule.rule_id)
        self.assertEqual(self.replica_bucket_name, rule.target_bucket_name)
        self.assertEqual(self.replica_endpoint, rule.target_bucket_location)
        self.assertEqual(self.transfer_type, rule.target_transfer_type)
        self.assertEqual(2, len(rule.prefix_list))
        self.assertTrue('prefix-1' in rule.prefix_list)
        self.assertTrue('prefix-2' in rule.prefix_list)
        self.assertEqual(1, len(rule.action_list))
        self.assertEqual(ReplicationRule.ALL, rule.action_list[0])
        self.assertTrue(rule.is_enable_historical_object_replication)
        self.assertEqual(ReplicationRule.STARTING, rule.status)
        self.assertEqual(self.sync_role_name, rule.sync_role_name)
        self.assertEqual(ReplicationRule.DISABLED, rule.sse_kms_encrypted_objects_status)
        # kms will be None
        self.assertIsNone(rule.replica_kms_keyid)


    def test_wrong_kms_encrypted_status(self):

        right_rule = ReplicationRule(target_bucket_name=self.replica_bucket_name,
                                         target_bucket_location=self.replica_endpoint,
                                         target_transfer_type=self.transfer_type,
                                         sse_kms_encrypted_objects_status=ReplicationRule.ENABLED)

        self.assertRaises(oss2.exceptions.ClientError, ReplicationRule, target_bucket_name=self.replica_bucket_name,
                          target_bucket_location=self.replica_endpoint, target_transfer_type=self.transfer_type,
                          sse_kms_encrypted_objects_status='wrong')

    def test_wrong_enable_historical_setting(self):
        right_rule = ReplicationRule(target_bucket_name=self.replica_bucket_name,
                                     target_bucket_location=self.replica_endpoint,
                                     target_transfer_type=self.transfer_type,
                                     is_enable_historical_object_replication=True)

        self.assertRaises(oss2.exceptions.ClientError, ReplicationRule, target_bucket_name=self.replica_bucket_name,
                          target_bucket_location=self.replica_endpoint, target_transfer_type=self.transfer_type,
                          is_enable_historical_object_replication='wrong')

    def test_replica_rule_id(self):
        self.assertRaises(oss2.exceptions.NoSuchReplicationRule, self.source_bucket.get_bucket_replication_progress, 'wrong')


if __name__ == '__main__':
    unittest.main()
