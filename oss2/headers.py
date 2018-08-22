# -*- coding: utf-8 -*-
"""
oss2.headers
~~~~~~~~
这个模块包含了发送http请求的header, 类型为dict
"""

OSS_SERVER_SIDE_ENCRYPTION = "x-oss-server-side-encryption"
OSS_SERVER_SIDE_ENCRYPTION_KEY_ID = "x-oss-server-side-encryption-key-id"

class requestHeader(dict): 
    def __init__(self, *arg, **kw): 
        super(requestHeader, self).__init__(*arg, **kw)

    def setServerSideEncryption(self, algorithm=None, cmk_id=None):
        if algorithm is "AES256":
            self[OSS_SERVER_SIDE_ENCRYPTION] = "AES256"

        elif algorithm is "KMS":
            self[OSS_SERVER_SIDE_ENCRYPTION] = "KMS"
            if cmk_id is not None:
                self[OSS_SERVER_SIDE_ENCRYPTION_KEY_ID] = cmk_id

        else:
            if OSS_SERVER_SIDE_ENCRYPTION in self:
                del self[OSS_SERVER_SIDE_ENCRYPTION]
            if OSS_SERVER_SIDE_ENCRYPTION_KEY_ID in self:
                del self[OSS_SERVER_SIDE_ENCRYPTION_KEY_ID]
