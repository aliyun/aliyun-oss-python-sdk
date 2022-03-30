# -*- coding: utf-8 -*-

from mock import patch
from unittests.common import *

class TestCloudBoxes(OssTestCase):

    @patch('oss2.Session.do_request')
    def test_list_cloud_boxes(self, do_request):

        request_text = '''GET /?cloudboxes HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Date: Fri, 24 Feb 2017 03:15:40 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
Authorization: OSS qn6qrrqxo2oawuk53otf****:PYbzsdWAIWAlMW8luk****'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:42 GMT
Content-Type: application/xml
Content-Length: 96
Connection: keep-alive
x-oss-request-id: 566B6BDD68248CE14F729DC0

<?xml version="1.0" encoding="UTF-8"?>
<ListCloudBoxResult>
    <Owner>
        <ID>1047205513514293</ID>
        <DisplayName>1047205513514293-NAME</DisplayName>
    </Owner>
    <Prefix>ap</Prefix>
    <Marker>ap-123123</Marker>
    <MaxKeys>1</MaxKeys>
    <IsTruncated>true</IsTruncated>
    <NextMarker>ap-123123</NextMarker>
    <CloudBoxs>
        <CloudBox>
            <Id>ap-123123</Id>
            <Name>cloudbox</Name>
            <Owner>
                <ID>111</ID>
                <DisplayName>222</DisplayName>
            </Owner>
            <Region>cn-hangzhou</Region>
            <ControlEndpoint>123.cn-hangzhou.oss-cloudbox-control.aliyuncs.com</ControlEndpoint>
            <DataEndpoint>123.cn-hangzhou.oss-cloudbox.aliyuncs.com</DataEndpoint>
        </CloudBox>
    </CloudBoxs>
</ListCloudBoxResult>'''

        req_info = mock_response(do_request, response_text)
        result = bucket().list_cloud_boxes()
        # result = bucket().list_cloud_boxes('1234','adb','10')

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.owner.id, '1047205513514293')
        self.assertEqual(result.owner.display_name, '1047205513514293-NAME')
        self.assertEqual(result.prefix, 'ap')
        self.assertEqual(result.marker, 'ap-123123')
        self.assertEqual(result.max_keys, 1)
        self.assertEqual(result.is_truncated, True)
        self.assertEqual(result.next_marker, 'ap-123123')
        self.assertEqual(result.cloud_boxes[0].id, 'ap-123123')
        self.assertEqual(result.cloud_boxes[0].name, 'cloudbox')
        self.assertEqual(result.cloud_boxes[0].region, 'cn-hangzhou')
        self.assertEqual(result.cloud_boxes[0].control_endpoint, '123.cn-hangzhou.oss-cloudbox-control.aliyuncs.com')
        self.assertEqual(result.cloud_boxes[0].data_endpoint, '123.cn-hangzhou.oss-cloudbox.aliyuncs.com')
        self.assertEqual(result.cloud_boxes[0].owner.id, '111')
        self.assertEqual(result.cloud_boxes[0].owner.display_name, '222')

if __name__ == '__main__':
    unittest.main()
