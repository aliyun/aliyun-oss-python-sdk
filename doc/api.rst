.. _api:

API文档
==========

.. module:: oss2

基础类
------

.. autoclass:: oss2.Auth
.. autoclass:: oss2.AnonymousAuth
.. autoclass:: oss2.StsAuth
.. autoclass:: oss2.Bucket
.. autoclass:: oss2.Service
.. autoclass:: oss2.Session

输入、输出和异常说明
------------------

.. automodule:: oss2.api

文件（Object）相关操作
--------------------

上传
~~~~
.. automethod:: oss2.Bucket.put_object
.. automethod:: oss2.Bucket.put_object_from_file
.. automethod:: oss2.Bucket.append_object


下载
~~~~
.. automethod:: oss2.Bucket.get_object
.. automethod:: oss2.Bucket.get_object_to_file


删除
~~~~
.. automethod:: oss2.Bucket.delete_object
.. automethod:: oss2.Bucket.batch_delete_objects


罗列
~~~~
.. automethod:: oss2.Bucket.list_objects

获取、更改文件信息
~~~~~~~~~~~~~~~

.. automethod:: oss2.Bucket.head_object
.. automethod:: oss2.Bucket.object_exists
.. automethod:: oss2.Bucket.put_object_acl
.. automethod:: oss2.Bucket.get_object_acl
.. automethod:: oss2.Bucket.update_object_meta
.. automethod:: oss2.Bucket.get_object_meta


分片上传
~~~~~~~~

.. automethod:: oss2.Bucket.init_multipart_upload
.. automethod:: oss2.Bucket.upload_part
.. automethod:: oss2.Bucket.complete_multipart_upload
.. automethod:: oss2.Bucket.abort_multipart_upload
.. automethod:: oss2.Bucket.list_multipart_uploads
.. automethod:: oss2.Bucket.list_parts


符号链接
~~~~~~~~

.. automethod:: oss2.Bucket.put_symlink
.. automethod:: oss2.Bucket.get_symlink


存储空间（Bucket）相关操作
-------------------------

创建、删除、查询
~~~~~~~~~~~~~~

.. automethod:: oss2.Bucket.create_bucket
.. automethod:: oss2.Bucket.delete_bucket
.. automethod:: oss2.Bucket.get_bucket_location

Bucket权限管理
~~~~~~~~~~~~~~
.. automethod:: oss2.Bucket.put_bucket_acl
.. automethod:: oss2.Bucket.get_bucket_acl


跨域资源共享（CORS）
~~~~~~~~~~~~~~~~~~~~
.. automethod:: oss2.Bucket.put_bucket_cors
.. automethod:: oss2.Bucket.get_bucket_cors
.. automethod:: oss2.Bucket.delete_bucket_cors


生命周期管理
~~~~~~~~~~~
.. automethod:: oss2.Bucket.put_bucket_lifecycle
.. automethod:: oss2.Bucket.get_bucket_lifecycle
.. automethod:: oss2.Bucket.delete_bucket_lifecycle


日志收集
~~~~~~~~

.. automethod:: oss2.Bucket.put_bucket_logging
.. automethod:: oss2.Bucket.get_bucket_logging
.. automethod:: oss2.Bucket.delete_bucket_logging

防盗链
~~~~~~

.. automethod:: oss2.Bucket.put_bucket_referer
.. automethod:: oss2.Bucket.get_bucket_referer

静态网站托管
~~~~~~~~~~~~

.. automethod:: oss2.Bucket.put_bucket_website
.. automethod:: oss2.Bucket.get_bucket_website
.. automethod:: oss2.Bucket.delete_bucket_website


RTPM推流操作
~~~~~~~~~~~~

.. automethod:: oss2.Bucket.create_live_channel
.. automethod:: oss2.Bucket.delete_live_channel
.. automethod:: oss2.Bucket.get_live_channel
.. automethod:: oss2.Bucket.list_live_channel
.. automethod:: oss2.Bucket.get_live_channel_stat
.. automethod:: oss2.Bucket.put_live_channel_status
.. automethod:: oss2.Bucket.get_live_channel_history
.. automethod:: oss2.Bucket.post_vod_playlist