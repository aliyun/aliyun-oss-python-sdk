# -*- coding: utf-8 -*-

import oss2

from functools import partial
from mock import patch

from common import *

UPLOAD_ID = '97BD544A65DB46F9A8735C93917A960F'


class TestMultipart(OssTestCase):
    @patch('oss2.Session.do_request')
    def test_init(self, do_request):
        body = '''<?xml version="1.0" encoding="UTF-8"?>
        <InitiateMultipartUploadResult>
          <Bucket>ming-oss-share</Bucket>
          <Key>uosvelpvgjwtxaciqtxoplnx</Key>
          <UploadId>{0}</UploadId>
        </InitiateMultipartUploadResult>
        '''.format(UPLOAD_ID)

        do_request.auto_spec = True
        do_request.side_effect = partial(do4body, body=body, content_type='application/xml')

        result = bucket().init_multipart_upload('fake-key')
        self.assertEqual(result.upload_id, UPLOAD_ID)

    @patch('oss2.Session.do_request')
    def test_upload_part(self, do_request):
        content = random_bytes(1024 * 1024 + 1)
        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4put_object, req_info=req_info, data_type=DT_BYTES)

        bucket().upload_part('fake-key', UPLOAD_ID, 3, content)

        self.assertEqual(content, req_info.data)
        self.assertEqual(req_info.req.params['partNumber'], '3')
        self.assertEqual(req_info.req.params['uploadId'], UPLOAD_ID)

    @patch('oss2.Session.do_request')
    def test_complete(self, do_request):
        from oss2.models import PartInfo

        parts = list()
        parts.append(PartInfo(2, '9433E6178C51CFEC867F592F4B827B50'))
        parts.append(PartInfo(3, '5570B91F31EBB06B6BA93BA6D63BE68A'))

        body = '''<?xml version="1.0" encoding="UTF-8"?>
        <CompleteMultipartUploadResult>
          <Location>http://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/fake-key</Location>
          <Bucket>ming-oss-share</Bucket>
          <Key>fake-key</Key>
          <ETag>"{0}-2"</ETag>
        </CompleteMultipartUploadResult>
        '''.format(ETAG)

        req_info = RequestInfo()
        do_request.auto_spec = True
        do_request.side_effect = partial(do4body, req_info=req_info, data_type=DT_BYTES, body=body)

        bucket().complete_multipart_upload('fake-key', UPLOAD_ID, parts)

        self.assertEqual(req_info.req.params['uploadId'], UPLOAD_ID)

        expected = b'<CompleteMultipartUpload><Part><PartNumber>2</PartNumber><ETag>"9433E6178C51CFEC867F592F4B827B50"</ETag></Part>' +\
                   b'<Part><PartNumber>3</PartNumber><ETag>"5570B91F31EBB06B6BA93BA6D63BE68A"</ETag></Part></CompleteMultipartUpload>'

        self.assertXmlEqual(expected, req_info.data)

    @patch('oss2.Session.do_request')
    def test_abort(self, do_request):
        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4delete, req_info=req_info)

        bucket().abort_multipart_upload('fake-key', UPLOAD_ID)

        self.assertEqual(req_info.req.params['uploadId'], UPLOAD_ID)

