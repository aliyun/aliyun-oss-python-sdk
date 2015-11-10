# Aliyun OSS SDK for Python

## 概述
阿里云对象存储Python SDK。

## 运行环境
Python 2.6，2.7，3.3，3.4，3.5

## 安装方法
```bash
$ pip install oss
```

## 快速使用
```python
import oss


auth = oss.Auth(access_key_id, access_key_secret)
bucket = oss.Bucket(auth, 'oss-cn-hangzhou.aliyuncs.com', 'my-bucket')

object_name = 'story.txt'

# 上传
bucket.put_object(object_name, 'Ali Baba is a happy youth.')

# 下载
bucket.get_object(object_name).read()

# 删除
bucket.delete_object(object_name)
```
## 测试
首先通过环境变量来设置测试所需的AccessKeyID、AccessKeySecret、Endpoint以及Bucket信息：
```bash
$ export OSS_TEST_ACCESS_KEY_ID=<AccessKeyID>
$ export OSS_TEST_ACCESS_KEY_SECRET=<AccessKeySecret>
$ export OSS_TEST_ENDPOINT=<endpoint>
$ export OSS_TEST_BUCKET=<bucket>
```
然后可以通过以下方式之一运行测试：
```bash
$ python -m unitest discover test   # 如果Python版本 >= 2.7
$ nosetests                         # 如果安装了nose
$ py.test                           # 如果安装了py.test
```
## 更多使用

## 注意事项

## 联系我们

## 代码许可
MIT许可证，参见LICENSE文件。