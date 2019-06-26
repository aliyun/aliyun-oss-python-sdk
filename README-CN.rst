Aliyun OSS SDK for Python
==========================

.. image:: https://badge.fury.io/py/oss2.svg
    :target: https://badge.fury.io/py/oss2
.. image:: https://travis-ci.org/aliyun/aliyun-oss-python-sdk.svg?branch=master
    :target: https://travis-ci.org/aliyun/aliyun-oss-python-sdk
.. image:: https://coveralls.io/repos/github/aliyun/aliyun-oss-python-sdk/badge.svg?branch=master
    :target: https://coveralls.io/github/aliyun/aliyun-oss-python-sdk?branch=master

`README of English <https://github.com/aliyun/aliyun-oss-python-sdk/blob/master/README.rst>`

概述
----

阿里云对象存储Python SDK 2.x版本。该版本不和上一个版本（0.x版本）兼容，包的名称为oss2，以避免和先前的版本冲突。


该版本的SDK依赖于第三方HTTP库 `requests <https://github.com/kennethreitz/requests>`_ 以及 `crcmod`。 请按照下述安装方法进行安装。

.. note::

    该版本不包含 `osscmd` 命令行工具

运行环境
--------

Python 2.6(不推荐)，2.7，3.3（不推荐），3.4，3.5，3.6

.. note::

    不推荐在Python 2.6版本运行oss2，因为现在官方已经不维护这个版本了
    请不要使用Python 3.3.0、3.3.1，参考 `Python Issue 16658 <https://bugs.python.org/issue16658>`_

安装方法
--------

通过pip安装官方发布的版本（以Linux系统为例）：

.. code-block:: bash

    $ pip install oss2

也可以直接安装解压后的安装包：

.. code-block:: bash

    $ sudo python setup.py install


快速使用
--------

.. code-block:: python

    # -*- coding: utf-8 -*-

    import oss2

    endpoint = 'http://oss-cn-hangzhou.aliyuncs.com' # 假设你的Bucket处于杭州区域

    auth = oss2.Auth('<你的AccessKeyId>', '<你的AccessKeySecret>')
    bucket = oss2.Bucket(auth, endpoint, '<你的Bucket名>')

    # Bucket中的文件名（key）为story.txt
    key = 'story.txt'

    # 上传
    bucket.put_object(key, 'Ali Baba is a happy youth.')

    # 下载
    bucket.get_object(key).read()

    # 删除
    bucket.delete_object(key)

    # 遍历Bucket里所有文件
    for object_info in oss2.ObjectIterator(bucket):
        print(object_info.key)

更多例子请参考examples目录下的代码。

出错处理
--------

除非特别说明，一旦出错，Python SDK的接口就会抛出异常（见oss2.exceptions子模块）。参考下面的例子：

.. code-block:: python

    try:
        result = bucket.get_object(key)
        print(result.read())
    except oss2.exceptions.NoSuchKey as e:
        print('{0} not found: http_status={1}, request_id={2}'.format(key, e.status, e.request_id))



设置日志
---------------
使用下面的代码可以设置oss2的日志级别.

.. code-block:: python

    import logging
    logging.getLogger('oss2').setLevel(logging.WARNING)

测试
----

首先通过环境变量来设置测试所需的AccessKeyId、AccessKeySecret、Endpoint以及Bucket信息（**请不要使用生产环境的Bucket**）。
以Linux系统为例：

.. code-block:: bash

    $ export OSS_TEST_ACCESS_KEY_ID=<AccessKeyId>
    $ export OSS_TEST_ACCESS_KEY_SECRET=<AccessKeySecret>
    $ export OSS_TEST_ENDPOINT=<endpoint>
    $ export OSS_TEST_BUCKET=<bucket>

    $ export OSS_TEST_STS_ID=<AccessKeyId for testing STS>
    $ export OSS_TEST_STS_KEY=<AccessKeySecret for testing STS>
    $ export OSS_TEST_STS_ARN=<Role ARN for testing STS>


然后通过以下方式运行测试：

.. code-block:: bash

    $ nosetests                          # 请先安装nose

更多使用
--------
- `更多例子 <https://github.com/aliyun/aliyun-oss-python-sdk/tree/master/examples>`_
- `Python SDK API文档 <http://aliyun-oss-python-sdk.readthedocs.org/en/latest>`_
- `官网Python SDK文档 <https://help.aliyun.com/document_detail/32026.html>`_

联系我们
--------
- `阿里云OSS官方网站 <http://oss.aliyun.com>`_
- `阿里云OSS官方论坛 <http://bbs.aliyun.com>`_
- `阿里云OSS官方文档中心 <https://help.aliyun.com/document_detail/32026.html>`_
- 阿里云官方技术支持：`提交工单 <https://workorder.console.aliyun.com/#/ticket/createIndex>`_

代码许可
--------
MIT许可证，参见LICENSE文件。
