import base64

from oss2.models import CallbackPolicyInfo
from .common import *

class TestBucketCallbackPolicy(OssTestCase):

    def test_callback_policy(self):

        # Set callback policy
        callback_content = "{\"callbackUrl\":\"www.abc.com/callback\",\"callbackBody\":\"${etag}\"}"
        callback_content2 = "{\"callbackUrl\":\"http://www.bbc.com/test\",\"callbackHost\":\"www.bbc.com\",\"callbackBody\":\"{\\\"mimeType\\\":${mimeType},\\\"size\\\":${size}}\"}"
        callback_var_content2 = "{\"x:var1\":\"value1\",\"x:var2\":\"value2\"}"
        callback = base64.b64encode(callback_content.encode(encoding='utf-8'))
        callback2 = base64.b64encode(callback_content2.encode(encoding='utf-8'))
        callback_var2 = base64.b64encode(callback_var_content2.encode(encoding='utf-8'))

        callback_policy_1 = CallbackPolicyInfo('test_1', callback)
        callback_policy_2 = CallbackPolicyInfo('test_2', callback2, callback_var2)
        put_result = self.bucket.put_bucket_callback_policy([callback_policy_1, callback_policy_2])
        self.assertEqual(200, put_result.status)


        # Get callback policy
        get_result = self.bucket.get_bucket_callback_policy()
        self.assertEqual(200, get_result.status)
        self.assertEqual(2, len(get_result.callback_policies))
        self.assertEqual('test_1', get_result.callback_policies[0].policy_name)
        self.assertEqual(callback.decode('utf-8'), get_result.callback_policies[0].callback)
        self.assertEqual('test_2', get_result.callback_policies[1].policy_name)
        self.assertEqual(callback2.decode('utf-8'), get_result.callback_policies[1].callback)
        self.assertEqual(callback_var2.decode('utf-8'), get_result.callback_policies[1].callback_var)

        # Upload File Trigger Callback
        self.bucket.put_object("test-key", "aaa", headers={'x-oss-callback': base64.b64encode("{\"callbackPolicy\":\"test_2\"}".encode(encoding='utf-8'))})

        # Delete callback policy
        del_result = self.bucket.delete_bucket_callback_policy()
        self.assertEqual(204, del_result.status)

        time.sleep(2)

        try:
            self.bucket.get_bucket_callback_policy()
        except oss2.exceptions.OssError as e:
            self.assertEqual("BucketCallbackPolicyNotExist", e.code)

    def test_callback_policy_exception_process(self):
        try:
            callback_policy_1 = ''
            callback_policy_2 = ''
            put_result = self.bucket.put_bucket_callback_policy([callback_policy_1, callback_policy_2])
            self.assertEqual(200, put_result.status)
        except Exception as e:
            self.assertEqual("'str' object has no attribute 'policy_name'", e.args[0])


        put_result = self.bucket.put_bucket_callback_policy(None)
        self.assertEqual(200, put_result.status)

        put_result = self.bucket.put_bucket_callback_policy([None, None])
        self.assertEqual(200, put_result.status)


if __name__ == '__main__':
    unittest.main()
