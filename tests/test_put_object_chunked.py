# -*- coding: utf-8 -*-

from .common import *
from oss2.compat import to_bytes


class TestPutObjectChunked(OssTestCase):
    def test_put_object_chunked(self):
        class FakeFileObj(object):
            def __init__(self, data, size):
                self.data = to_bytes(data)
                self.offset = 0
                self.size = size

            def read(self, amt=None):
                if self.offset >= self.size:
                    return to_bytes('')

                if amt is None or amt < 0:
                    bytes_to_read = self.size - self.offset
                else:
                    bytes_to_read = min(amt, self.size - self.offset)

                content = self.data[self.offset:self.offset + bytes_to_read]

                self.offset += bytes_to_read

                return content

        object_name = 'test-put-file-like-object-chunked'

        count = 1
        while count <= 1500:
            try:
                count += 1

                cnt = random.randint(count, 102400)
                data = FakeFileObj(b'a' * cnt, count)
                self.bucket.put_object(object_name + str(count) + '.txt', data)
                cnt = random.randint(count, 102400)
                data = FakeFileObj(b'a' * cnt, cnt)
                self.bucket.put_object(object_name + str(count) + '11.txt', data)
            except oss2.exceptions.ServerError as e:
                if e.code == 'BadRequest':
                    raise
            except Exception:
                continue


if __name__ == '__main__':
    unittest.main()
