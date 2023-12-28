# -*- coding: utf-8 -*-

import unittest
import oss2
from oss2.auth import *
from oss2.credentials import *


class TestAuth(unittest.TestCase):
    def test_auth_version(self):
        provider = StaticCredentialsProvider('ak', 'sk')
        auth1 = ProviderAuth(provider)
        self.assertEqual('v1', auth1.auth_version())

        auth2 = ProviderAuthV2(provider)
        self.assertEqual('v2', auth2.auth_version())

        auth4 = ProviderAuthV4(provider)
        self.assertEqual('v4', auth4.auth_version())

        auth = Auth('ak', 'sk')
        self.assertEqual('v1', auth.auth_version())

        auth = AuthV2('ak', 'sk')
        self.assertEqual('v2', auth.auth_version())

        auth = AuthV4('ak', 'sk')
        self.assertEqual('v4', auth.auth_version())

        stsauth = StsAuth('ak', 'sk', 'token', AUTH_VERSION_1)
        self.assertEqual('v1', stsauth.auth_version())

        stsauth = StsAuth('ak', 'sk', 'token', AUTH_VERSION_2)
        self.assertEqual('v2', stsauth.auth_version())

        stsauth = StsAuth('ak', 'sk', 'token', AUTH_VERSION_4)
        self.assertEqual('v4', stsauth.auth_version())

        stsauth = StsAuth('ak', 'sk', 'token')
        self.assertEqual('v1', stsauth.auth_version())

if __name__ == '__main__':
    unittest.main()
