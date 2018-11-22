Alibaba Cloud OSS SDK for Python
================================

.. image:: https://badge.fury.io/py/oss2.svg
    :target: https://badge.fury.io/py/oss2
.. image:: https://travis-ci.org/aliyun/aliyun-oss-python-sdk.svg?branch=master
    :target: https://travis-ci.org/aliyun/aliyun-oss-python-sdk
.. image:: https://coveralls.io/repos/github/aliyun/aliyun-oss-python-sdk/badge.svg?branch=master
    :target: https://coveralls.io/github/aliyun/aliyun-oss-python-sdk?branch=master

`README of Chinese <https://github.com/aliyun/aliyun-oss-python-sdk/blob/master/README-CN.rst>`_    
------------------

Overview
--------

Alibaba Cloud Object Storage Python SDK 2.x. This version is not compatible with the previous version (Version 0.x). The package name is `oss2` to avoid conflict with previous versions. 


The SDK of this version is dependent on the third-party HTTP library `requests <https://github.com/kennethreitz/requests>`_ and `crcmod`. Install the SDK following the methods below. 

Note:

    This version does not contain the `osscmd` command line tool. 

Running environment
-------------------

Python 2.6，2.7，3.3，3.4，3.5

Note:

    Do not use Python 3.3.0 or 3.3.1. Refer to `Python Issue 16658 <https://bugs.python.org/issue16658>`_.

Installing
----------

Install the official release version through PIP (taking Linux as an example): 

.. code-block:: bash

    $ pip install oss2

You can also install the unzipped installer package directly: 

.. code-block:: bash

    $ sudo python setup.py install


Getting started
---------------

.. code-block:: python

    # -*- coding: utf-8 -*-

    import oss2

    endpoint = 'http://oss-cn-hangzhou.aliyuncs.com' # Suppose that your bucket is in the Hangzhou region. 

    auth = oss2.Auth('<Your AccessKeyID>', '<Your AccessKeySecret>')
    bucket = oss2.Bucket(auth, endpoint, '<your bucket name>')

    # The object key in the bucket is story.txt
    key = 'story.txt'

    # Upload
    bucket.put_object(key, 'Ali Baba is a happy youth.')

    # Download
    bucket.get_object(key).read()

    # Delete
    bucket.delete_object(key)

    # Traverse all objects in the bucket
    for object_info in oss2.ObjectIterator(bucket):
        print(object_info.key)

For more examples, refer to the code under the "examples" directory. 

Handling errors
---------------

The Python SDK interface will throw an exception in case of an error (see oss2.exceptions sub-module) unless otherwise specified. An example is provided below:

.. code-block:: python

    try:
        result = bucket.get_object(key)
        print(result.read())
    except oss2.exceptions.NoSuchKey as e:
        print('{0} not found: http_status={1}, request_id={2}'.format(key, e.status, e.request_id))

Setup Logging
---------------

By default, a logger named oss2 with INFO level is enabled. Following code can change the default logging level.

.. code-block:: python

    import logging
    logging.getLogger('oss2').setLevel(logging.WARNING)

Testing
-------

First set the required AccessKeyId, AccessKeySecret, endpoint and bucket information for the test through environment variables (**Do not use the bucket for the production environment**). 
Take the Linux system for example: 

.. code-block:: bash

    $ export OSS_TEST_ACCESS_KEY_ID=<AccessKeyId>
    $ export OSS_TEST_ACCESS_KEY_SECRET=<AccessKeySecret>
    $ export OSS_TEST_ENDPOINT=<endpoint>
    $ export OSS_TEST_BUCKET=<bucket>

    $ export OSS_TEST_STS_ID=<AccessKeyId for testing STS>
    $ export OSS_TEST_STS_KEY=<AccessKeySecret for testing STS>
    $ export OSS_TEST_STS_ARN=<Role ARN for testing STS>


Run the test in the following method: 

.. code-block:: bash

    $ nosetests                          # First install nose


You can set environment variable to test auth v2:

.. code-block:: bash

    $ export OSS_TEST_AUTH_VERSION=v2

More resources
--------------
- `More examples <https://github.com/aliyun/aliyun-oss-python-sdk/tree/master/examples>`_. 
- `Python SDK API documentation <http://aliyun-oss-python-sdk.readthedocs.org/en/latest>`_. 
- `Official Python SDK documentation <https://help.aliyun.com/document_detail/32026.html>`_.

Contacting us
-------------
- `Alibaba Cloud OSS official website <http://oss.aliyun.com>`_.
- `Alibaba Cloud OSS official forum <http://bbs.aliyun.com>`_.
- `Alibaba Cloud OSS official documentation center <https://help.aliyun.com/document_detail/32026.html>`_.
- Alibaba Cloud official technical support: `Submit a ticket <https://workorder.console.aliyun.com/#/ticket/createIndex>`_.

License
-------
- `MIT <https://github.com/aliyun/aliyun-oss-python-sdk/blob/master/LICENSE>`_.
