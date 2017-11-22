from test_object import TestObject
import os
import oss2

TestSign = TestObject
"""
这个类主要是用来增加测试覆盖率，当环境变量为oss2.SIGN_VERSION_2，则重新设置为oss2.SIGN_VERSION_1再运行TestObject，反之亦然
"""
if __name__ == '__main__':
    if os.getenv('OSS_TEST_AUTH_VERSION') == oss2.SIGN_VERSION_2:
        os.environ['OSS_TEST_AUTH_VERSION'] = oss2.SIGN_VERSION_1
    else:
        os.environ['OSS_TEST_AUTH_VERSION'] = oss2.SIGN_VERSION_2

    from common import *
    unittest.main()
