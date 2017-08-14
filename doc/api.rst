.. _api:

API document
==========

.. module:: oss2

Base classes
------

.. autoclass:: oss2.Auth
.. autoclass:: oss2.AnonymousAuth
.. autoclass:: oss2.StsAuth
.. autoclass:: oss2.Bucket
.. autoclass:: oss2.Service
.. autoclass:: oss2.Session

Input, Output and Exceptions
------------------

.. automodule:: oss2.api

Object operations
--------------------

Upload
~~~~
.. automethod:: oss2.Bucket.put_object
.. automethod:: oss2.Bucket.put_object_from_file
.. automethod:: oss2.Bucket.append_object


Download
~~~~
.. automethod:: oss2.Bucket.get_object
.. automethod:: oss2.Bucket.get_object_to_file


Delete
~~~~
.. automethod:: oss2.Bucket.delete_object
.. automethod:: oss2.Bucket.batch_delete_objects


List
~~~~
.. automethod:: oss2.Bucket.list_objects

Get/Update file information
~~~~~~~~~~~~~~~

.. automethod:: oss2.Bucket.head_object
.. automethod:: oss2.Bucket.object_exists
.. automethod:: oss2.Bucket.put_object_acl
.. automethod:: oss2.Bucket.get_object_acl
.. automethod:: oss2.Bucket.update_object_meta
.. automethod:: oss2.Bucket.get_object_meta


Multipart upload
~~~~~~~~

.. automethod:: oss2.Bucket.init_multipart_upload
.. automethod:: oss2.Bucket.upload_part
.. automethod:: oss2.Bucket.complete_multipart_upload
.. automethod:: oss2.Bucket.abort_multipart_upload
.. automethod:: oss2.Bucket.list_multipart_uploads
.. automethod:: oss2.Bucket.list_parts


Symlink
~~~~~~~~

.. automethod:: oss2.Bucket.put_symlink
.. automethod:: oss2.Bucket.get_symlink


Bucket operations
-------------------------

Create, Delete, Query
~~~~~~~~~~~~~~

.. automethod:: oss2.Bucket.create_bucket
.. automethod:: oss2.Bucket.delete_bucket
.. automethod:: oss2.Bucket.get_bucket_location

Bucket ACL
~~~~~~~~~~~~~~
.. automethod:: oss2.Bucket.put_bucket_acl
.. automethod:: oss2.Bucket.get_bucket_acl


CORS (cross origin resource sharing)
~~~~~~~~~~~~~~~~~~~~
.. automethod:: oss2.Bucket.put_bucket_cors
.. automethod:: oss2.Bucket.get_bucket_cors
.. automethod:: oss2.Bucket.delete_bucket_cors


Lifecycle management
~~~~~~~~~~~
.. automethod:: oss2.Bucket.put_bucket_lifecycle
.. automethod:: oss2.Bucket.get_bucket_lifecycle
.. automethod:: oss2.Bucket.delete_bucket_lifecycle


Logging
~~~~~~~~

.. automethod:: oss2.Bucket.put_bucket_logging
.. automethod:: oss2.Bucket.get_bucket_logging
.. automethod:: oss2.Bucket.delete_bucket_logging

Referrer
~~~~~~

.. automethod:: oss2.Bucket.put_bucket_referer
.. automethod:: oss2.Bucket.get_bucket_referer

Static website
~~~~~~~~~~~~

.. automethod:: oss2.Bucket.put_bucket_website
.. automethod:: oss2.Bucket.get_bucket_website
.. automethod:: oss2.Bucket.delete_bucket_website


RTPM pushing streaming operations
~~~~~~~~~~~~

.. automethod:: oss2.Bucket.create_live_channel
.. automethod:: oss2.Bucket.delete_live_channel
.. automethod:: oss2.Bucket.get_live_channel
.. automethod:: oss2.Bucket.list_live_channel
.. automethod:: oss2.Bucket.get_live_channel_stat
.. automethod:: oss2.Bucket.put_live_channel_status
.. automethod:: oss2.Bucket.get_live_channel_history
.. automethod:: oss2.Bucket.post_vod_playlist