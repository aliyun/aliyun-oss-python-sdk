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


断点续传上传
~~~~~~~~~~~~

.. autofunction:: oss2.resumable_upload


FileObject适配器
~~~~~~~~~~~~~~~~~~

.. autoclass:: oss2.SizedStreamReader
.. autoclass:: oss2.MonitoredStreamReader