.. _easy:


易用性接口
==========

.. module:: oss2

迭代器
~~~~~~

.. autoclass:: oss2.BucketIterator
.. autoclass:: oss2.ObjectIterator
.. autoclass:: oss2.MultipartUploadIterator
.. autoclass:: oss2.ObjectUploadIterator
.. autoclass:: oss2.PartIterator


断点续传（上传、下载）
~~~~~~~~~~~~~~~~~~~

.. autofunction:: oss2.resumable_upload
.. autofunction:: oss2.resumable_download

FileObject适配器
~~~~~~~~~~~~~~~~~~

.. autoclass:: oss2.SizedFileAdapter