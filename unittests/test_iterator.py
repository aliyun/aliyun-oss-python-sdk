# -*- coding: utf-8 -*-

from mock import patch
from unittests.common import *

from oss2.models import SimplifiedBucketInfo, SimplifiedObjectInfo
from oss2 import to_string


class TestIterator(OssTestCase):
    def assertInstanceEqual(self, a, b):
        adict = vars(a)
        bdict = vars(b)

        for k, v in adict.items():
            self.assertEqual(adict[k], bdict[k])

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
              <ExtranetEndpoint>oss-cn-hangzhou.aliyuncs.com</ExtranetEndpoint>
              <IntranetEndpoint>oss-cn-hangzhou-internal.aliyuncs.com</IntranetEndpoint>
              <Location>oss-cn-hangzhou</Location>
              <Name>bucket-1</Name>
              <StorageClass>Standard</StorageClass>
            </Bucket>
            <Bucket>
              <CreationDate>2015-12-11T09:01:57.000Z</CreationDate>
              <ExtranetEndpoint>oss-us-west-1.aliyuncs.com</ExtranetEndpoint>
              <IntranetEndpoint>oss-us-west-internal-1.aliyuncs.com</IntranetEndpoint>
              <Location>oss-us-west-1</Location>
              <Name>bucket-2</Name>
              <StorageClass>Standard</StorageClass>
            </Bucket>
          </Buckets>
        </ListAllMyBucketsResult>
        ''']

        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = make_do4body(req_infos=[req_info], body_list=body_list)

        expected = [SimplifiedBucketInfo('bucket-1', 'oss-cn-hangzhou', 1449880531, 'oss-cn-hangzhou.aliyuncs.com',
                                         'oss-cn-hangzhou-internal.aliyuncs.com', 'Standard'),
                    SimplifiedBucketInfo('bucket-2', 'oss-us-west-1', 1449824517, 'oss-us-west-1.aliyuncs.com',
                                         'oss-us-west-internal-1.aliyuncs.com', 'Standard')]

        got = list(oss2.BucketIterator(service()))

        self.assertEqual(len(expected), len(got))
        self.assertInstanceEqual(expected[0], got[0])
        self.assertInstanceEqual(expected[1], got[1])

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
              <StorageClass>Standard</StorageClass>
            </Bucket>
            <Bucket>
              <CreationDate>2014-09-06T13:20:33.000Z</CreationDate>
              <ExtranetEndpoint>oss-cn-hangzhou.aliyuncs.com</ExtranetEndpoint>
              <IntranetEndpoint>oss-cn-hangzhou-internal.aliyuncs.com</IntranetEndpoint>
              <Location>oss-cn-hangzhou</Location>
              <Name>ming-oss-share</Name>
              <StorageClass>Standard</StorageClass>
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
              <StorageClass>Standard</StorageClass>
            </Bucket>
            <Bucket>
              <CreationDate>2015-06-29T13:43:52.000Z</CreationDate>
              <ExtranetEndpoint>oss-cn-hangzhou.aliyuncs.com</ExtranetEndpoint>
              <IntranetEndpoint>oss-cn-hangzhou-internal.aliyuncs.com</IntranetEndpoint>
              <Location>oss-cn-hangzhou</Location>
              <Name>ming-spike</Name>
              <StorageClass>Standard</StorageClass>
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
              <StorageClass>Standard</StorageClass>
            </Bucket>
          </Buckets>
        </ListAllMyBucketsResult>''']

        expected = [SimplifiedBucketInfo('ming-bj', 'oss-cn-beijing', 1450854535, 'oss-cn-beijing.aliyuncs.com',
                                         'oss-cn-beijing-internal.aliyuncs.com', 'Standard'),
                    SimplifiedBucketInfo('ming-oss-share', 'oss-cn-hangzhou', 1410009633, 'oss-cn-hangzhou.aliyuncs.com'
                                         , 'oss-cn-hangzhou-internal.aliyuncs.com', 'Standard'),
                    SimplifiedBucketInfo('ming-qd', 'oss-cn-qingdao', 1451017363, 'oss-cn-qingdao.aliyuncs.com',
                                         'oss-cn-qingdao-internal.aliyuncs.com', 'Standard'),
                    SimplifiedBucketInfo('ming-spike', 'oss-cn-hangzhou', 1435585432, 'oss-cn-hangzhou.aliyuncs.com'
                                         , 'oss-cn-hangzhou-internal.aliyuncs.com', 'Standard'),
                    SimplifiedBucketInfo('zzy-share', 'oss-cn-hangzhou',1450187570, 'oss-cn-hangzhou.aliyuncs.com'
                                         , 'oss-cn-hangzhou-internal.aliyuncs.com', 'Standard')]

        nreq = 3

        req_infos = [RequestInfo() for i in range(nreq)]

        do_request.auto_spec = True
        do_request.side_effect = make_do4body(req_infos=req_infos, body_list=body_list)

        got = list(oss2.BucketIterator(service(), max_keys=2))

        self.assertEqual(len(expected), len(got))

        for i in range(len(got)):
            self.assertInstanceEqual(expected[i], got[i])

        for i in range(nreq):
            self.assertEqual(req_infos[i].req.params.get('max-keys'), '2')
            self.assertEqual(req_infos[i].req.params.get('prefix', ''), '')

        self.assertEqual(req_infos[0].req.params.get('marker', ''), '')
        self.assertEqual(req_infos[1].req.params.get('marker', ''), 'ming-oss-share')
        self.assertEqual(req_infos[2].req.params.get('marker', ''), 'ming-spike')

    @patch('oss2.Session.do_request')
    def test_object_iterator_empty(self, do_request):
        body_list = [b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult>
          <Name>ming-bj</Name>
          <Prefix></Prefix>
          <Marker></Marker>
          <MaxKeys>1000</MaxKeys>
          <Delimiter></Delimiter>
          <EncodingType>url</EncodingType>
          <IsTruncated>false</IsTruncated>
        </ListBucketResult>''']

        do_request.auto_spec = True
        do_request.side_effect = make_do4body(body_list=body_list)

        got = list(oss2.ObjectIterator(bucket(), max_keys=1000))
        self.assertEqual(len(got), 0)

    @patch('oss2.Session.do_request')
    def test_object_iterator_not_truncated(self, do_request):
        body_list = [b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult>
          <Name>zzy-share</Name>
          <Prefix></Prefix>
          <Marker></Marker>
          <MaxKeys>1000</MaxKeys>
          <Delimiter></Delimiter>
          <IsTruncated>false</IsTruncated>
          <Contents>
            <Key>object-1</Key>
            <LastModified>2015-02-02T05:15:13.000Z</LastModified>
            <ETag>"716AF6FFD529DFEA856FAA4E12D2C5EA"</ETag>
            <Type>Normal</Type>
            <Size>4308</Size>
            <StorageClass>Standard</StorageClass>
            <Owner>
              <ID>1047205513514293</ID>
              <DisplayName>1047205513514293</DisplayName>
            </Owner>
          </Contents>
          <Contents>
            <Key>object-2</Key>
            <LastModified>2015-06-23T09:56:55.000Z</LastModified>
            <ETag>"333D74B47CB1B0E275D2AB3CDDA02665-26"</ETag>
            <Type>Multipart</Type>
            <Size>3389246</Size>
            <StorageClass>Standard</StorageClass>
            <Owner>
              <ID>1047205513514293</ID>
              <DisplayName>1047205513514293</DisplayName>
            </Owner>
          </Contents>
          <Contents>
            <Key>object-3</Key>
            <LastModified>2015-01-16T12:41:34.000Z</LastModified>
            <ETag>"B28F7255E6EA777DB0AFB1C58C2CFCFE"</ETag>
            <Type>Normal</Type>
            <Size>10718416</Size>
            <StorageClass>Standard</StorageClass>
            <Owner>
              <ID>1047205513514293</ID>
              <DisplayName>1047205513514293</DisplayName>
            </Owner>
          </Contents>
        </ListBucketResult>
        ''']

        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = make_do4body(req_infos=[req_info], body_list=body_list)

        got = list(oss2.ObjectIterator(bucket(), max_keys=1000))

        expected = [SimplifiedObjectInfo('object-1', 1422854113, '716AF6FFD529DFEA856FAA4E12D2C5EA', 'Normal', 4308, 'Standard'),
                    SimplifiedObjectInfo('object-2', 1435053415, '333D74B47CB1B0E275D2AB3CDDA02665-26', 'Multipart', 3389246, 'Standard'),
                    SimplifiedObjectInfo('object-3', 1421412094, 'B28F7255E6EA777DB0AFB1C58C2CFCFE', 'Normal', 10718416, 'Standard')]

        self.assertEqual(len(expected), len(got))

        for i in range(len(expected)):
            self.assertInstanceEqual(expected[i], got[i])

        self.assertEqual(req_info.req.params.get('prefix', ''), '')
        self.assertEqual(req_info.req.params.get('marker', ''), '')
        self.assertEqual(req_info.req.params.get('encoding-type'), 'url')

    @patch('oss2.Session.do_request')
    def test_object_iterator_truncated(self, do_request):
        body_list = [b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult>
          <Name>ming-spike</Name>
          <Prefix></Prefix>
          <Marker></Marker>
          <MaxKeys>1</MaxKeys>
          <Delimiter></Delimiter>
          <EncodingType>url</EncodingType>
          <IsTruncated>true</IsTruncated>
          <NextMarker>a.txt</NextMarker>
          <Contents>
            <Key>a.txt</Key>
            <LastModified>2016-01-07T11:10:00.000Z</LastModified>
            <ETag>"5EB63BBBE01EEED093CB22BB8F5ACDC3"</ETag>
            <Type>Normal</Type>
            <Size>11</Size>
            <StorageClass>Standard</StorageClass>
            <Owner>
              <ID>1047205513514293</ID>
              <DisplayName>1047205513514293</DisplayName>
            </Owner>
          </Contents>
        </ListBucketResult>''',
        b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult>
          <Name>ming-spike</Name>
          <Prefix></Prefix>
          <Marker>a.txt</Marker>
          <MaxKeys>1</MaxKeys>
          <Delimiter></Delimiter>
          <EncodingType>url</EncodingType>
          <IsTruncated>true</IsTruncated>
          <NextMarker>%E4%B8%AD%E6%96%87.txt</NextMarker>
          <Contents>
            <Key>%E4%B8%AD%E6%96%87.txt</Key>
            <LastModified>2016-01-07T11:09:39.000Z</LastModified>
            <ETag>"FC3FF98E8C6A0D3087D515C0473F8677"</ETag>
            <Type>Normal</Type>
            <Size>12</Size>
            <StorageClass>Standard</StorageClass>
            <Owner>
              <ID>1047205513514293</ID>
              <DisplayName>1047205513514293</DisplayName>
            </Owner>
          </Contents>
        </ListBucketResult>''',
        b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult>
          <Name>ming-spike</Name>
          <Prefix></Prefix>
          <Marker>%E4%B8%AD%E6%96%87.txt</Marker>
          <MaxKeys>1</MaxKeys>
          <Delimiter></Delimiter>
          <EncodingType>url</EncodingType>
          <IsTruncated>false</IsTruncated>
          <Contents>
            <Key>%E9%98%BF%E9%87%8C%E4%BA%91.txt</Key>
            <LastModified>2016-01-07T11:07:32.000Z</LastModified>
            <ETag>"5D41402ABC4B2A76B9719D911017C592"</ETag>
            <Type>Normal</Type>
            <Size>5</Size>
            <StorageClass>Standard</StorageClass>
            <Owner>
              <ID>1047205513514293</ID>
              <DisplayName>1047205513514293</DisplayName>
            </Owner>
          </Contents>
        </ListBucketResult>''']

        expected = [SimplifiedObjectInfo('a.txt', 1452165000, '5EB63BBBE01EEED093CB22BB8F5ACDC3', 'Normal', 11, 'Standard'),
                    SimplifiedObjectInfo('中文.txt', 1452164979, 'FC3FF98E8C6A0D3087D515C0473F8677', 'Normal', 12, 'Standard'),
                    SimplifiedObjectInfo('阿里云.txt', 1452164852, '5D41402ABC4B2A76B9719D911017C592', 'Normal', 5, 'Standard')]

        nreq = 3

        req_infos = [RequestInfo() for i in range(nreq)]

        do_request.auto_spec = True
        do_request.side_effect = make_do4body(req_infos=req_infos, body_list=body_list)

        got = list(oss2.ObjectIterator(bucket(), max_keys=1))

        for i in range(len(expected)):
            self.assertInstanceEqual(expected[i], got[i])

        for i in range(nreq):
            self.assertEqual(req_infos[i].req.params.get('prefix', ''), '')
            self.assertEqual(req_infos[i].req.params.get('max-keys', ''), '1')
            self.assertEqual(req_infos[i].req.params.get('delimiter', ''), '')
            self.assertEqual(req_infos[i].req.params.get('encoding-type', ''), 'url')

        self.assertEqual(req_infos[0].req.params.get('marker', ''), '')
        self.assertEqual(req_infos[1].req.params.get('marker', ''), 'a.txt')
        self.assertEqual(req_infos[2].req.params.get('marker', ''), '中文.txt')

    @patch('oss2.Session.do_request')
    def test_object_iterator_dir(self, do_request):
        body_list=[b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult>
          <Name>ming-spike</Name>
          <Prefix></Prefix>
          <Marker></Marker>
          <MaxKeys>1000</MaxKeys>
          <Delimiter>%2F</Delimiter>
          <EncodingType>url</EncodingType>
          <IsTruncated>false</IsTruncated>
          <Contents>
            <Key>a.txt</Key>
            <LastModified>2016-01-07T11:10:00.000Z</LastModified>
            <ETag>"5EB63BBBE01EEED093CB22BB8F5ACDC3"</ETag>
            <Type>Normal</Type>
            <Size>11</Size>
            <StorageClass>Standard</StorageClass>
            <Owner>
              <ID>1047205513514293</ID>
              <DisplayName>1047205513514293</DisplayName>
            </Owner>
          </Contents>
          <CommonPrefixes>
            <Prefix>%E6%96%87%E4%BB%B6%2F</Prefix>
          </CommonPrefixes>
        </ListBucketResult>''']

        expected = [SimplifiedObjectInfo('a.txt', 1452165000, '5EB63BBBE01EEED093CB22BB8F5ACDC3', 'Normal', 11, 'Standard'),
                    SimplifiedObjectInfo('文件/', None, None, None, None, None)]

        req_info = RequestInfo()
        do_request.auto_spec = True
        do_request.side_effect = make_do4body(req_infos=[req_info], body_list=body_list)

        got = list(oss2.ObjectIterator(bucket(), max_keys=1000))

        for i in range(len(expected)):
            self.assertInstanceEqual(expected[i], got[i])

    @patch('oss2.Session.do_request')
    def test_upload_iterator_empty(self, do_request):
        body_list = [b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListMultipartUploadsResult>
          <EncodingType>url</EncodingType>
          <Bucket>ming-spike</Bucket>
          <KeyMarker></KeyMarker>
          <UploadIdMarker></UploadIdMarker>
          <NextKeyMarker></NextKeyMarker>
          <NextUploadIdMarker></NextUploadIdMarker>
          <Delimiter></Delimiter>
          <Prefix></Prefix>
          <MaxUploads>1000</MaxUploads>
          <IsTruncated>false</IsTruncated>
        </ListMultipartUploadsResult>''']

        do_request.auto_spec = True
        do_request.side_effect = make_do4body(body_list=body_list)

        got = list(oss2.MultipartUploadIterator(bucket(), max_uploads=1000))
        self.assertEqual(len(got), 0)

    def test_part_iterator_default_max_retries(self):
        iter = oss2.PartIterator(bucket(), 'fake-key', 'fake-upload-id')
        self.assertEqual(iter.max_retries, oss2.defaults.request_retries)

        oss2.defaults.request_retries = 100
        iter = oss2.PartIterator(bucket(), 'fake-key', 'fake-upload-id')
        self.assertEqual(iter.max_retries, 100)

        iter = oss2.PartIterator(bucket(), 'fake-key', 'fake-upload-id', max_retries=1)
        self.assertEqual(iter.max_retries, 1)

    def test_object_iterator_default_max_retries(self):
        iter = oss2.ObjectIterator(bucket())
        self.assertEqual(iter.max_retries, oss2.defaults.request_retries)

        oss2.defaults.request_retries = 100
        iter = oss2.ObjectIterator(bucket())
        self.assertEqual(iter.max_retries, 100)

        iter = oss2.ObjectIterator(bucket(), max_retries=1)
        self.assertEqual(iter.max_retries, 1)

    def test_bucket_iterator_default_max_retries(self):
        iter = oss2.BucketIterator(service())
        self.assertEqual(iter.max_retries, oss2.defaults.request_retries)

        oss2.defaults.request_retries = 100
        iter = oss2.BucketIterator(service())
        self.assertEqual(iter.max_retries, 100)

        iter = oss2.BucketIterator(service(), max_retries=1)
        self.assertEqual(iter.max_retries, 1)

    def test_object_upload_iterator_default_max_retries(self):
        iter = oss2.ObjectUploadIterator(bucket(), 'fake-key')
        self.assertEqual(iter.max_retries, oss2.defaults.request_retries)

        oss2.defaults.request_retries = 100
        iter = oss2.ObjectUploadIterator(bucket(), 'fake-key')
        self.assertEqual(iter.max_retries, 100)

        iter = oss2.ObjectUploadIterator(bucket(), 'fake-key', max_retries=1)
        self.assertEqual(iter.max_retries, 1)


if __name__ == '__main__':
    unittest.main()