# -*- coding: utf-8 -*-

import unittest
import oss2
from oss2.headers import *


class TestHeaders(unittest.TestCase):
    def test_check_RequestHeader(self):
        myHeader = RequestHeader()
        
        myHeader.set_server_side_encryption(algorithm="AES256")
        self.assertTrue(myHeader["x-oss-server-side-encryption"] is "AES256")

        myHeader.set_server_side_encryption(algorithm="KMS", cmk_id="1111")
        self.assertTrue(myHeader["x-oss-server-side-encryption"] is "KMS")
        self.assertTrue(myHeader["x-oss-server-side-encryption-key-id"] is "1111")

        myHeader.set_server_side_encryption(algorithm="aaa")
        self.assertTrue("x-oss-server-side-encryption" not in myHeader)
        self.assertTrue("x-oss-server-side-encryption-key-id" not in myHeader)

