# -*- coding: utf-8 -*-

import unittest
import oss2
from oss2.headers import *


class TestHeaders(unittest.TestCase):
    def test_check_requestHeader(self):
        myHeader = requestHeader()
        
        myHeader.setServerSideEncryption(algorithm="AES256")
        self.assertTrue(myHeader["x-oss-server-side-encryption"] is "AES256")

        myHeader.setServerSideEncryption(algorithm="KMS", cmk_id="1111")
        self.assertTrue(myHeader["x-oss-server-side-encryption"] is "KMS")
        self.assertTrue(myHeader["x-oss-server-side-encryption-key-id"] is "1111")

        myHeader.setServerSideEncryption(algorithm="aaa")
        self.assertTrue("x-oss-server-side-encryption" not in myHeader)
        self.assertTrue("x-oss-server-side-encryption-key-id" not in myHeader)

