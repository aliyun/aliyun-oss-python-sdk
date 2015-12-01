.. _easy:


易用性接口
==========

.. module:: oss

迭代器
~~~~~~

.. autoclass:: oss.BucketIterator
.. autoclass:: oss.ObjectIterator
.. autoclass:: oss.MultipartUploadIterator
.. autoclass:: oss.ObjectUploadIterator
.. autoclass:: oss.PartIterator


断点续传上传
~~~~~~~~~~~~

.. autofunction:: oss.resumable_upload


FileObject适配器
~~~~~~~~~~~~~~~~~~

.. autoclass:: oss.SizedStreamReader
.. autoclass:: oss.MonitoredStreamReader