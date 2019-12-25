# -*- coding: utf-8 -*-

import unittest
import xml.etree.ElementTree as ElementTree
from oss2.xml_utils import _find_tag, _find_bool
from oss2.xml_utils import parse_get_bucket_info
from .common import MockResponse
import oss2


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
                <Comment>test</Comment>
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


if __name__ == '__main__':
    unittest.main()