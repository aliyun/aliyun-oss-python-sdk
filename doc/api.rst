.. _api:

API文档
==========

.. module:: oss

基础类
------

.. autoclass:: oss.Auth
.. autoclass:: oss.AnonymousAuth
.. autoclass:: oss.Bucket
.. autoclass:: oss.Service
.. autoclass:: oss.Session

文件（Object）相关操作
--------------------

上传
~~~~
.. automethod:: oss.Bucket.put_object
.. automethod:: oss.Bucket.put_object_from_file
.. automethod:: oss.Bucket.append_object


下载
~~~~
.. automethod:: oss.Bucket.get_object
.. automethod:: oss.Bucket.get_object_to_file


删除
~~~~
.. automethod:: oss.Bucket.delete_object
.. automethod:: oss.Bucket.batch_delete_objects


罗列
~~~~
.. automethod:: oss.Bucket.list_objects

获取文件信息
~~~~~~~~~~~~

.. automethod:: oss.Bucket.head_object
.. automethod:: oss.Bucket.object_exists


分片上传
~~~~~~~~

.. automethod:: oss.Bucket.init_multipart_upload
.. automethod:: oss.Bucket.upload_part
.. automethod:: oss.Bucket.complete_multipart_upload
.. automethod:: oss.Bucket.abort_multipart_upload
.. automethod:: oss.Bucket.list_multipart_uploads
.. automethod:: oss.Bucket.list_parts


存储空间（Bucket）相关操作
-------------------------

创建、删除、查询
~~~~~~~~~~~~~~

.. automethod:: oss.Bucket.create_bucket
.. automethod:: oss.Bucket.delete_bucket
.. automethod:: oss.Bucket.bucket_exists
.. automethod:: oss.Bucket.get_bucket_location

Bucket权限管理
~~~~~~~~~~~~~~
.. automethod:: oss.Bucket.put_bucket_acl
.. automethod:: oss.Bucket.get_bucket_acl


跨域资源共享（CORS）
~~~~~~~~~~~~~~~~~~~~
.. automethod:: oss.Bucket.put_bucket_cors
.. automethod:: oss.Bucket.get_bucket_cors
.. automethod:: oss.Bucket.delete_bucket_cors


对象生命周期管理
~~~~~~~~~~~~~~~~
.. automethod:: oss.Bucket.put_bucket_lifecycle
.. automethod:: oss.Bucket.get_bucket_lifecycle
.. automethod:: oss.Bucket.delete_bucket_lifecycle


日志收集
~~~~~~~~

.. automethod:: oss.Bucket.put_bucket_logging
.. automethod:: oss.Bucket.get_bucket_logging
.. automethod:: oss.Bucket.delete_bucket_logging

防盗链
~~~~~~

.. automethod:: oss.Bucket.put_bucket_referer
.. automethod:: oss.Bucket.get_bucket_referer

静态网站托管
~~~~~~~~~~~~

.. automethod:: oss.Bucket.put_bucket_website
.. automethod:: oss.Bucket.get_bucket_website
.. automethod:: oss.Bucket.delete_bucket_website

