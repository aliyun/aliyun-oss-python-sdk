# -*- coding: utf-8 -*-

import unittest
import xml.etree.ElementTree as ElementTree
import oss2
from oss2.models import ReplicationRule
from oss2.xml_utils import _find_tag, _find_bool
from oss2.xml_utils import (parse_get_bucket_info,
                            parse_get_bucket_replication_result,
                            parse_get_bucket_replication_location_result,
                            parse_get_bucket_replication_progress_result)
from .common import MockResponse



class TestXmlUtils(unittest.TestCase):
    def test_find_tag(self):
        body = '''
        <Test>
            <Grant>private</Grant>
        </Test>'''

        root = ElementTree.fromstring(body)

        grant = _find_tag(root, 'Grant')
        self.assertEqual(grant, 'private')

        self.assertRaises(RuntimeError, _find_tag, root, 'none_exist_tag')

    def test_find_bool(self):
        body = '''
        <Test>
            <BoolTag1>true</BoolTag1>
            <BoolTag2>false</BoolTag2>
        </Test>'''

        root = ElementTree.fromstring(body)

        tag1 = _find_bool(root, 'BoolTag1')
        tag2 = _find_bool(root, 'BoolTag2')
        self.assertEqual(tag1, True)
        self.assertEqual(tag2, False)

        self.assertRaises(RuntimeError, _find_bool, root, 'none_exist_tag')

    def test_parse_get_bucket_info(self):
        body = '''
        <BucketInfo>
            <Bucket>
                <CreationDate>2013-07-31T10:56:21.000Z</CreationDate>
                <ExtranetEndpoint>oss-cn-hangzhou.aliyuncs.com</ExtranetEndpoint>
                <IntranetEndpoint>oss-cn-hangzhou-internal.aliyuncs.com</IntranetEndpoint>
                <Location>oss-cn-hangzhou</Location>
                <Name>oss-example</Name>
                <StorageClass>IA</StorageClass>
                <Owner>
                    <DisplayName>username</DisplayName>
                    <ID>27183473914****</ID>
                </Owner>
                <AccessControlList>
                    <Grant>private</Grant>
                </AccessControlList>
            </Bucket>
        </BucketInfo>
        '''
        headers = oss2.CaseInsensitiveDict({
            'Server': 'AliyunOSS',
            'Date': 'Fri, 11 Dec 2015 11:40:30 GMT',
            'Content-Length': len(body),
            'Connection': 'keep-alive',
            'x-oss-request-id': '566AB62EB06147681C283D73',
            'ETag': '7AE1A589ED6B161CAD94ACDB98206DA6'
        })
        resp =  MockResponse(200, headers, body)

        result = oss2.models.GetBucketInfoResult(resp)
        parse_get_bucket_info(result, body)
        self.assertEqual(result.location, 'oss-cn-hangzhou')
        self.assertIsNone(result.data_redundancy_type)
        self.assertIsNone(result.comment)
        self.assertIsNone(result.versioning_status)
        self.assertIsNone(result.bucket_encryption_rule)

    def test_parse_get_bucket_replication(self):
        body = '''<ReplicationConfiguration>
  <Rule>
    <ID>test_replication_1</ID>
    <PrefixSet>
      <Prefix>source_image</Prefix>
      <Prefix>video</Prefix>
    </PrefixSet>
    <Action>PUT</Action>
    <Destination>
      <Bucket>target-bucket</Bucket>
      <Location>oss-ap-south-1</Location>
      <TransferType>oss_acc</TransferType>
    </Destination>
    <Status>doing</Status>
    <HistoricalObjectReplication>enabled</HistoricalObjectReplication>
    <SyncRole>aliyunramrole</SyncRole>
    <SourceSelectionCriteria>
      <SseKmsEncryptedObjects>
        <Status>Enabled</Status>
      </SseKmsEncryptedObjects>
    </SourceSelectionCriteria>
    <EncryptionConfiguration>
      <ReplicaKmsKeyID>c2ee80d6-1111-1111-1111-a3644797b566</ReplicaKmsKeyID>
    </EncryptionConfiguration>
  </Rule>
</ReplicationConfiguration>
        '''
        headers = oss2.CaseInsensitiveDict({
            'Server': 'AliyunOSS',
            'Date': 'Fri, 11 Dec 2015 11:40:30 GMT',
            'Content-Length': len(body),
            'Connection': 'keep-alive',
            'x-oss-request-id': '566AB62EB06147681C283D73',
            'ETag': '7AE1A589ED6B161CAD94ACDB98206DA6'
        })
        resp = MockResponse(200, headers, body)

        result = oss2.models.GetBucketReplicationResult(resp)
        parse_get_bucket_replication_result(result, body)
        self.assertEqual(1, len(result.rule_list))
        rule = result.rule_list[0]

        self.assertEqual('test_replication_1', rule.rule_id)
        self.assertEqual('target-bucket', rule.target_bucket_name)
        self.assertEqual('oss-ap-south-1', rule.target_bucket_location)
        self.assertEqual('oss_acc', rule.target_transfer_type)
        self.assertEqual(2, len(rule.prefix_list))
        self.assertTrue('source_image' in rule.prefix_list)
        self.assertTrue('video' in rule.prefix_list)
        self.assertEqual(1, len(rule.action_list))
        self.assertEqual('PUT', rule.action_list[0])
        self.assertTrue(rule.is_enable_historical_object_replication)
        self.assertEqual(ReplicationRule.DOING, rule.status)
        self.assertEqual('aliyunramrole', rule.sync_role_name)
        self.assertEqual('c2ee80d6-1111-1111-1111-a3644797b566', rule.replica_kms_keyid)
        self.assertEqual('Enabled', rule.sse_kms_encrypted_objects_status)

    def test_parse_get_bucket_replication_location(self):
        body = '''<ReplicationLocation>
  <Location>oss-cn-beijing</Location>
  <Location>oss-cn-qingdao</Location>
  <Location>oss-cn-shenzhen</Location>
  <Location>oss-cn-hongkong</Location>
  <Location>oss-us-west-1</Location>
  <LocationTransferTypeConstraint>
    <LocationTransferType>
      <Location>oss-cn-hongkong</Location>
        <TransferTypes>
          <Type>oss_acc</Type>          
        </TransferTypes>
      </LocationTransferType>
      <LocationTransferType>
        <Location>oss-us-west-1</Location>
        <TransferTypes>
          <Type>oss_acc</Type>
        </TransferTypes>
      </LocationTransferType>
    </LocationTransferTypeConstraint>
  </ReplicationLocation>'''
        headers = oss2.CaseInsensitiveDict({
            'Server': 'AliyunOSS',
            'Date': 'Fri, 11 Dec 2015 11:40:30 GMT',
            'Content-Length': len(body),
            'Connection': 'keep-alive',
            'x-oss-request-id': '566AB62EB06147681C283D73',
            'ETag': '7AE1A589ED6B161CAD94ACDB98206DA6'
        })
        resp = MockResponse(200, headers, body)

        result = oss2.models.GetBucketReplicationLocationResult(resp)
        parse_get_bucket_replication_location_result(result, body)
        self.assertEqual(5, len(result.location_list))
        self.assertTrue('oss-cn-beijing' in result.location_list)
        self.assertTrue('oss-cn-qingdao' in result.location_list)
        self.assertTrue('oss-cn-shenzhen' in result.location_list)
        self.assertTrue('oss-cn-hongkong' in result.location_list)
        self.assertTrue('oss-us-west-1' in result.location_list)
        self.assertEqual(2, len(result.location_transfer_type_list))
        self.assertTrue('oss-cn-hongkong' in [result.location_transfer_type_list[0].location,
                                              result.location_transfer_type_list[1].location])
        self.assertTrue('oss-us-west-1' in [result.location_transfer_type_list[0].location,
                                            result.location_transfer_type_list[1].location])
        self.assertEqual('oss_acc', result.location_transfer_type_list[0].transfer_type)
        self.assertEqual('oss_acc', result.location_transfer_type_list[1].transfer_type)

    def test_parse_get_bucket_replication_progress(self):
        body = '''<ReplicationProgress>
 <Rule>
   <ID>test_replication_1</ID>
   <PrefixSet>
    <Prefix>source_image</Prefix>
    <Prefix>video</Prefix>
   </PrefixSet>
   <Action>PUT,ABORT,DELETE</Action>
   <Destination>
    <Bucket>target-bucket</Bucket>
    <Location>oss-cn-beijing</Location>
    <TransferType>oss_acc</TransferType>
   </Destination>
   <Status>doing</Status>
   <HistoricalObjectReplication>enabled</HistoricalObjectReplication>
   <Progress>
    <HistoricalObject>0.85</HistoricalObject>
    <NewObject>2015-09-24T15:28:14.000Z</NewObject>
   </Progress>
 </Rule>
</ReplicationProgress>'''
        headers = oss2.CaseInsensitiveDict({
            'Server': 'AliyunOSS',
            'Date': 'Fri, 11 Dec 2015 11:40:30 GMT',
            'Content-Length': len(body),
            'Connection': 'keep-alive',
            'x-oss-request-id': '566AB62EB06147681C283D73',
            'ETag': '7AE1A589ED6B161CAD94ACDB98206DA6'
        })
        resp = MockResponse(200, headers, body)

        result = oss2.models.GetBucketReplicationProgressResult(resp)
        parse_get_bucket_replication_progress_result(result, body)
        progress = result.progress
        self.assertEqual('test_replication_1', progress.rule_id)
        self.assertEqual('target-bucket', progress.target_bucket_name)
        self.assertEqual('oss-cn-beijing', progress.target_bucket_location)
        self.assertEqual('oss_acc', progress.target_transfer_type)
        self.assertEqual(2, len(progress.prefix_list))
        self.assertTrue('source_image' in progress.prefix_list)
        self.assertTrue('video' in progress.prefix_list)

        self.assertEqual(3, len(progress.action_list))
        self.assertTrue('PUT' in progress.action_list)
        self.assertTrue('DELETE' in progress.action_list)
        self.assertTrue('ABORT' in progress.action_list)
        self.assertTrue(progress.is_enable_historical_object_replication)
        self.assertEqual('doing', progress.status)
        self.assertEqual(0.85, progress.historical_object_progress)
        self.assertEqual('2015-09-24T15:28:14.000Z', progress.new_object_progress)


if __name__ == '__main__':
    unittest.main()

