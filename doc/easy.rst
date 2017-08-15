.. _easy:


interfaces for easy to use
==========

.. module:: oss2

Iterators
~~~~~~

.. autoclass:: oss2.BucketIterator
.. autoclass:: oss2.ObjectIterator
.. autoclass:: oss2.MultipartUploadIterator
.. autoclass:: oss2.ObjectUploadIterator
.. autoclass:: oss2.PartIterator


Resumable upload or download.
~~~~~~~~~~~~~~~~~~~

.. autofunction:: oss2.resumable_upload
.. autofunction:: oss2.resumable_download

FileObject Adapter
~~~~~~~~~~~~~~~~~~

.. autoclass:: oss2.SizedFileAdapter