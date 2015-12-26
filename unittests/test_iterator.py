# -*- coding: utf-8 -*-

from mock import patch
from common import *

from oss2.models import SimplifiedBucketInfo


class TestIterator(OssTestCase):
    def assertBucketEqual(self, a, b):
        self.assertEqual(a.name, b.name)
        self.assertEqual(a.location, b.location)
        self.assertEqual(a.creation_date, b.creation_date)

    @patch('oss2.Session.do_request')
    def test_bucket_iterator_not_truncated(self, do_request):
        body_list = [b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListAllMyBucketsResult>
          <Owner>
            <ID>1047205513514293</ID>
            <DisplayName>1047205513514293</DisplayName>
          </Owner>
          <Buckets>
            <Bucket>
              <CreationDate>2015-12-12T00:35:31.000Z</CreationDate>
              <Location>oss-cn-hangzhou</Location>
              <Name>bucket-1</Name>
            </Bucket>
            <Bucket>
              <CreationDate>2015-12-11T09:01:57.000Z</CreationDate>
              <Location>oss-us-west-1</Location>
              <Name>bucket-2</Name>
            </Bucket>
          </Buckets>
        </ListAllMyBucketsResult>
        ''']

        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = make_do4body(req_infos=[req_info], body_list=body_list)

        expected = [SimplifiedBucketInfo('bucket-1', 'oss-cn-hangzhou', 1449880531),
                    SimplifiedBucketInfo('bucket-2', 'oss-us-west-1', 1449824517)]

        got = list(oss2.BucketIterator(service()))

        self.assertEqual(len(expected), len(got))
        self.assertBucketEqual(expected[0], got[0])
        self.assertBucketEqual(expected[1], got[1])

        self.assertEqual(req_info.req.params.get('prefix', ''), '')
        self.assertEqual(req_info.req.params.get('marker', ''), '')

    @patch('oss2.Session.do_request')
    def test_bucket_iterator_truncated(self, do_request):
        body_list = [b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListAllMyBucketsResult>
          <Owner>
            <ID>1047205513514293</ID>
            <DisplayName>1047205513514293</DisplayName>
          </Owner>
          <Buckets>
            <Bucket>
              <CreationDate>2015-12-23T07:08:55.000Z</CreationDate>
              <ExtranetEndpoint>oss-cn-beijing.aliyuncs.com</ExtranetEndpoint>
              <IntranetEndpoint>oss-cn-beijing-internal.aliyuncs.com</IntranetEndpoint>
              <Location>oss-cn-beijing</Location>
              <Name>ming-bj</Name>
            </Bucket>
            <Bucket>
              <CreationDate>2014-09-06T13:20:33.000Z</CreationDate>
              <ExtranetEndpoint>oss-cn-hangzhou.aliyuncs.com</ExtranetEndpoint>
              <IntranetEndpoint>oss-cn-hangzhou-internal.aliyuncs.com</IntranetEndpoint>
              <Location>oss-cn-hangzhou</Location>
              <Name>ming-oss-share</Name>
            </Bucket>
          </Buckets>
          <Prefix></Prefix>
          <Marker></Marker>
          <MaxKeys>1</MaxKeys>
          <IsTruncated>true</IsTruncated>
          <NextMarker>ming-oss-share</NextMarker>
        </ListAllMyBucketsResult>''',

        b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListAllMyBucketsResult>
          <Owner>
            <ID>1047205513514293</ID>
            <DisplayName>1047205513514293</DisplayName>
          </Owner>
          <Buckets>
            <Bucket>
              <CreationDate>2015-12-25T04:22:43.000Z</CreationDate>
              <ExtranetEndpoint>oss-cn-qingdao.aliyuncs.com</ExtranetEndpoint>
              <IntranetEndpoint>oss-cn-qingdao-internal.aliyuncs.com</IntranetEndpoint>
              <Location>oss-cn-qingdao</Location>
              <Name>ming-qd</Name>
            </Bucket>
            <Bucket>
              <CreationDate>2015-06-29T13:43:52.000Z</CreationDate>
              <ExtranetEndpoint>oss-cn-hangzhou.aliyuncs.com</ExtranetEndpoint>
              <IntranetEndpoint>oss-cn-hangzhou-internal.aliyuncs.com</IntranetEndpoint>
              <Location>oss-cn-hangzhou</Location>
              <Name>ming-spike</Name>
            </Bucket>
          </Buckets>
          <Prefix></Prefix>
          <Marker>ming-oss-share</Marker>
          <MaxKeys>2</MaxKeys>
          <IsTruncated>true</IsTruncated>
          <NextMarker>ming-spike</NextMarker>
        </ListAllMyBucketsResult>''',

        b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListAllMyBucketsResult>
          <Owner>
            <ID>1047205513514293</ID>
            <DisplayName>1047205513514293</DisplayName>
          </Owner>
          <Buckets>
            <Bucket>
              <CreationDate>2015-12-15T13:52:50.000Z</CreationDate>
              <ExtranetEndpoint>oss-cn-hangzhou.aliyuncs.com</ExtranetEndpoint>
              <IntranetEndpoint>oss-cn-hangzhou-internal.aliyuncs.com</IntranetEndpoint>
              <Location>oss-cn-hangzhou</Location>
              <Name>zzy-share</Name>
            </Bucket>
          </Buckets>
        </ListAllMyBucketsResult>''']

        expected = [SimplifiedBucketInfo('ming-bj', 'oss-cn-beijing', 1450854535),
                    SimplifiedBucketInfo('ming-oss-share', 'oss-cn-hangzhou', 1410009633),
                    SimplifiedBucketInfo('ming-qd', 'oss-cn-qingdao', 1451017363),
                    SimplifiedBucketInfo('ming-spike', 'oss-cn-hangzhou', 1435585432),
                    SimplifiedBucketInfo('zzy-share', 'oss-cn-hangzhou',1450187570)]

        nreq = 3

        req_infos = [RequestInfo() for i in range(nreq)]

        do_request.auto_spec = True
        do_request.side_effect = make_do4body(req_infos=req_infos, body_list=body_list)

        got = list(oss2.BucketIterator(service(), max_keys=2))

        self.assertEqual(len(expected), len(got))

        for i in range(len(got)):
            self.assertBucketEqual(expected[i], got[i])

        for i in range(nreq):
            self.assertEqual(req_infos[i].req.params.get('max-keys'), '2')
            self.assertEqual(req_infos[i].req.params.get('prefix', ''), '')

        self.assertEqual(req_infos[0].req.params.get('marker', ''), '')
        self.assertEqual(req_infos[1].req.params.get('marker', ''), 'ming-oss-share')
        self.assertEqual(req_infos[2].req.params.get('marker', ''), 'ming-spike')
