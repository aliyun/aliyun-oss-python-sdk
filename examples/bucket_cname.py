
import os
import oss2

# Specify access information, such as AccessKeyId, AccessKeySecret, and Endpoint.
# You can obtain access information from evironment variables or replace sample values in the code, such as <your AccessKeyId> with actual values.
#
# For example, if your bucket is located in the China (Hangzhou) region, you can set Endpoint to one of the following values:
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com


access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<yourAccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<yourAccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<yourBucketName>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<yourEndpoint>')

test_domain = 'www.example.com'
cert_id = '49311111-cn-hangzhou'
previous_cert_id = '493333'
certificate = '''-----BEGIN CERTIFICATE-----
MIIDWzCCAkOgAwIBA***uYSSkW+KTgnwyOGU9cv+mxA=
-----END CERTIFICATE-----'''
private_key = '''-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqh***2t41Q/SC3HUGC5mJjpO8=
-----END PRIVATE KEY-----
'''


# Make sure that all parameters are correctly configured
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, 'Please set parameters：' + param


# Create a bucket. You can use the bucket to call all object-related operations
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# Create cnametoken required for domain name ownership verification
result = bucket.create_bucket_cname_token(test_domain)
print(result.cname)
print(result.token)
print(result.expire_time)

# Get the created cnametoken.
get_result = bucket.bucket.get_bucket_cname_token(test_domain)
print(get_result.cname)
print(get_result.token)
print(get_result.expire_time)

# Bind a custom domain name to a bucket.
cert = oss2.models.CertInfo(cert_id, certificate, private_key, previous_cert_id, True, False)
input = oss2.models.PutBucketCnameRequest(test_domain, cert)
bucket.put_bucket_cname(input)

# Query the list of all cnames bound under a storage space (bucket).
list_result = bucket.list_bucket_cname()
for c in list_result.cname:
    print(c.domain)
    print(c.last_modified)
    print(c.status)

# Delete the bound CNAME of a storage space (bucket)
bucket.delete_bucket_cname(test_domain)