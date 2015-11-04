import os
import random
import string


OSS_ID = os.getenv("OSS_TEST_ACCESS_KEY_ID")
OSS_SECRET = os.getenv("OSS_TEST_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_TEST_ENDPOINT")
OSS_BUCKET = os.getenv("OSS_TEST_BUCKET")


def random_string(n):
    return ''.join(random.choice(string.letters) for i in xrange(n))