# -*- coding: utf-8 -*-

import unittest
import xml.etree.ElementTree as ElementTree
from oss2.xml_utils import _find_tag, _find_bool


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


if __name__ == '__main__':
    unittest.main()