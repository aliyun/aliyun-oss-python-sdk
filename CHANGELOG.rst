OSS SDK for Python Release record
===========================

Python SDK version follows `Semantic Versioning <http://semver.org/>`.

Version 2.3.3
-------------

- Fix：No in RequestResult.resp and the link does not work.


Version 2.3.2
-------------

- Fix：issue #70


Version 2.3.1
-------------

- Fix：issue #63 Add `oss2.defaults.logger` config. The default one is 'root logger'.
- Fix：issue #66 oss2 related Adapter uses __len__()function which leads to requests super_len() cannot handle file with more than 2GB size in 32 bit Windows.


Version 2.3.0
-------------

- Add：APIs `bucket.put_symlink`，`bucket.get_symlink`


Version 2.2.3
-------------

- Fix：The return value of `bucket.resumable_upload` is corrected as PutObjectResult from null.
- Fix：Improves the way concatenanting string in  `Response.read` which improves the efficiency of `bucket.get_object`. Issue #39.
- Fix：Uses the url encoding for source key in `bucket.copy_object`.


Version 2.2.2
-------------

- Fix：Add header parameters in upload_part.


Version 2.2.1
-------------

- Fix：Only does the CRC64 integrity check when x-oss-hash-crc64ecma is returned from OSS.


Version 2.2.0
-------------

- Dependency：Add a new dependency `crcmod`
- Add：Enable CRC (by default) in upload and download.
- Add：`RTMP` pushing streaming related APIs
- Add：`bucket.get_object_meta()` API for getting basic metadata.
- Fix：`bucket.object_exists()` API is re-implemented with `bucket.get_object_meta()` to solve the "retrieve from source" impact. issue #39

Version 2.1.1
-------------

- Fix：issue #28。
- Fix：Sets a correct connection pool size.


Version 2.1.0
-------------

- Add：Add a property `oss2.defaults.connection_pool_size` to set the max connection count in connection pool.
- Add：Add the parameter `num_threads` in `oss2.resumable_upload` to specify the thread number of uploading.
- Add：Add `oss2.resumable_download` to resume a download.
- Fix：The checkpoint file name should be generated from normalized local file name; when the checkpoint file is not in JSON format, delete the checkpoint file.
- Fix：Fix some documents bug.

Version 2.0.6
-------------

- Add：Support STS authentication by `StsAuth` class.
- Add：Add Travis CI support.
- Update：Initial version of unit test.

Version 2.0.5
-------------

- Add：The default connect timeout is changed to 60s from 10s. To be compatible with older request library (< 2.4.0), the connect timeout and read timeout share the same value.
       This is to avoid the read timeout in CopyObject、UploadPartCopy因read timeout.
- Add：Add `security-token` into sub resources and get signed.
- Fix：User could set properties in oss2.defaults to change the default value.

Version 2.0.4
-------------

- Update：Add the folder of unittests. The tests folder now becomes functional tests. Tox runs unittest by default.
- Fix：Remove the dependency of requests 2.9.0. This is due to `Issue 2844 <https://github.com/kennethreitz/requests/issues/2844>`, which leads to UTF-8 data transfer issue.
- Fix：OSS server should return InvalidObjectName error instead of SignatureDoesNotMatch when Object name starts with '/'. The fix is to url encode the '/' in URL.
- Fix：Correct the README.rst in MANIFEST.in.



Version 2.0.3
-------------

- Redesign the Python SDK. The original offical SDK of version 0.x.x is deprecated.
- Only supports Python2.6 or higher, supports Python 3 as well.
- Adds the dependency on request library.
