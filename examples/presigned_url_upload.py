# examples/presigned_url_upload.py

import oss2

# Replace with your actual credentials and bucket info
ACCESS_KEY_ID = '<your-access-key-id>'
ACCESS_KEY_SECRET = '<your-access-key-secret>'
ENDPOINT = 'https://oss-cn-hangzhou.aliyuncs.com'  # Change if needed
BUCKET_NAME = '<your-bucket-name>'
OBJECT_NAME = 'demo_upload_via_presigned.txt'
EXPIRATION_SECONDS = 300  # 5 minutes

# Initialize auth and bucket
auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, ENDPOINT, BUCKET_NAME)

# Generate presigned URL for PUT upload
signed_url = bucket.sign_url('PUT', OBJECT_NAME, EXPIRATION_SECONDS)

print("✅ Presigned URL (valid for 5 minutes):")
print(signed_url)

# Optional upload using requests
try:
    import requests
    with open('example.txt', 'rb') as f:
        response = requests.put(signed_url, data=f)
        print("Upload status code:", response.status_code)
except Exception as e:
    print("Install `requests` to auto-upload, or use the URL manually.")
