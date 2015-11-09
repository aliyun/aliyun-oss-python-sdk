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

## 更多使用

## 注意事项

## 联系我们

## 代码许可
MIT许可证，参见LICENSE文件。