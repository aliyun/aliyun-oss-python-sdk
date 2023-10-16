from .common import *

class TestWriteGetObjectResponse(OssTestCase):


    def test_write_get_object_response_normal(self):

        # The fc function returns route
        route = "test-ap-zxl-process-name-43-1283641064516515-opap.oss-cn-beijing-internal.oss-object-process.aliyuncs.com"
        # The fc function returns token
        token = "CAISgQJ1q6Ft5B2yfSjIr5DFE/7HiepJj6ugYUv5jzdgO8tnhZLNtjz2IHxMdHJsCeAcs/Q0lGFR5/sflrEtFsUUHBDqPJNewMh8qCr7PqOb45eewOBcYi8hpLLKWXDBx8b3T7jTbrG0I4WACT3tkit03sGJF1GLVECkNpukkINuas9tMCCzcTtBAqU9RGIg0rh4U0HcLvGwKBXnr3PNBU5zwGpGhHh49L60z7/3iHOcriWjkL9O%2Bdioesb4MpAyYc4iabrvgrwqLJim%2BTVL9h1H%2BJ1xiKF54jrdtrmfeQINu0Xdb7qEqIA/d18oP/lnRrQmtvH5kuZjpuHIi5RmB9P71C6/ORqAAS1lAA7hnd1vUHQxjsCeTLBccf9wgeDefOqht46RyE5pxroD0XyHG1Jj/25HuSvGcwGUafW7hLCup3x4wzeL9aDOX%2BE6Pd4yPqQrk6%2BX%2BXYyFWxhxVXrUyQ18MkgI65mDkY8pN9Jysg2sdTjxwxAkfzqTf62DVuCuaAzktvLps18IAA%3D&Expires=1697191658&OSSAccessKeyId=STS.NSpXDsd5h8iKcmHk757DKjWfT&Signature=obyMgdG7SpRpp%2FJB3eEqRT7dlC0%3D"

        fwd_status = '200'
        content = 'a' * 1024

        headers = dict()
        headers['x-oss-fwd-header-Content-Type'] = 'application/octet-stream'
        headers['x-oss-fwd-header-ETag'] = 'testetag'


        service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), route)
        try:
            # testing is only supported in FC
            result = service.write_get_object_response(route, token, fwd_status, content, headers)
        except oss2.exceptions.RequestError as e:
            pass



if __name__ == '__main__':
    unittest.main()
