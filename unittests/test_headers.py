# -*- coding: utf-8 -*-

import unittest
import oss2
from oss2.headers import *


class TestHeaders(unittest.TestCase):
    def test_check_requestHeader(self):
        myHeader = requestHeader()
        
        myHeader.setServerSideEncryption(algorithm="AES256")
        self.assertTrue(myHeader[OSS_SERVER_SIDE_ENCRYPTION] is "AES256")

        myHeader.setServerSideEncryption(algorithm="KMS", cmk_id="1111")
        self.assertTrue(myHeader[OSS_SERVER_SIDE_ENCRYPTION] is "KMS")
        self.assertTrue(myHeader[OSS_SERVER_SIDE_ENCRYPTION_KEY_ID] is "1111")

        myHeader.setServerSideEncryption(algorithm="aaa")
        self.assertTrue(OSS_SERVER_SIDE_ENCRYPTION not in myHeader)
        self.assertTrue(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID not in myHeader)

