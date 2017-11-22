# -*- coding: utf-8 -*-

from test_object import TestObject
from common import *


def empty_func():
    pass


class TestSign(TestObject):
    """
        这个类主要是用来增加测试覆盖率，当环境变量为oss2.SIGN_VERSION_2，则重新设置为oss2.SIGN_VERSION_1再运行TestObject，反之亦然
    """
    def __init__(self, *args, **kwargs):
        super(TestSign, self).__init__(*args, **kwargs)

    def setUp(self):
        if os.getenv('OSS_TEST_AUTH_VERSION') == oss2.SIGN_VERSION_2:
            os.environ['OSS_TEST_AUTH_VERSION'] = oss2.SIGN_VERSION_1
        else:
            os.environ['OSS_TEST_AUTH_VERSION'] = oss2.SIGN_VERSION_2
        super(TestSign, self).setUp()

    def tearDown(self):
        if os.getenv('OSS_TEST_AUTH_VERSION') == oss2.SIGN_VERSION_2:
            os.environ['OSS_TEST_AUTH_VERSION'] = oss2.SIGN_VERSION_1
        else:
            os.environ['OSS_TEST_AUTH_VERSION'] = oss2.SIGN_VERSION_2
        super(TestSign, self).tearDown()


if __name__ == '__main__':
    unittest.main()
