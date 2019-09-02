OSS SDK for Python 版本记录
===========================

Python SDK的版本号遵循 `Semantic Versioning <http://semver.org/>`_ 规则。

Version 2.8.0
-------------
- 增加：Request Payment 接口，支持访问者付费请求
- 增加：服务端限速设置接口，支持上传下载限速功能
- 增加：Routing Rule 接口，支持设置跳转或者镜像回源规则
- 优化：对部分bucket API 添加content-md5

Version 2.7.0
-------------
- 增加：SelectObjct 接口 支持 byte range 查询
- 增加：对象标签( Object Tagging) 功能
- 增加：Bucket Encryption 接口
- 增加：多版本(Versioning) 功能
- 增加：Bucket Policy 接口

Version 2.6.1
-------------

- 修复: 不指定默认的日志级别
- 修复: 修复日志中存在的中文标点符号的问题
- 增加: 帮助文档增加如何设置日志级别的方法说明
- 修复: 当传入的playlist为空时，不指定playlist为生成推流签名的url的参数
- 修复: 初始化LiveChannelInfo实例时，使用默认的构造函数初始化target成员
- 修复: 有些调试信息的日志，修改成debug级别，避免过多的日志打印

Version 2.6.0
-------------

- 增加: 添加详细的log输出
- 增加: 断点下载支持crc校验
- 增加: ipv6支持
- 增加: 使用签名URL上传下载
- 增加: 服务端加密支持传入CMK ID
- 增加: select查询接口支持
- 修复: list bucket支持返回extranet endpoint & interanet enpoint & storage class
- 修复: upload_part_copy接口支持中文等特殊字符对象的拷贝
- 修复: get_object接口带'range'的http header时不校验crc
- 修复: get_object接口带'Accept-Encoding'的http header且值为'gzip'时不校验crc

Version 2.5.0
-------------

- 增加：支持客户端加密

Version 2.4.0
-------------

- 增加：`bucket.create_bucket` 支持创建IA/Archive类型的存储空间
- 增加：`bucket.restore_object` 解冻Archive类型的文件
- 增加：`bucket.get_bucket_info`，`bucket.get_bucket_stat` 获取存储空间相关的信息
- 增加：LifeCycle支持CreatedBeforeDate，AbortMultipartUpload和IA/Archive

Version 2.3.4
-------------

- 修复：issue #64 #73 #82 #87


Version 2.3.3
-------------

- 修复：RequestResult.resp没有read，链接无法重用


Version 2.3.2
-------------

- 修复：issue #70


Version 2.3.1
-------------

- 修复：#63 增加 `oss2.defaults.logger` 配置项，用户可以设置该变量，来改变缺省的 `logger` （缺省是 `root` logger）
- 修复：#66 oss2相关的Adapter中用了__len__()函数会导致requests super_len()函数在32bit Windows上导致不能够上传超过2GB的文件。


Version 2.3.0
-------------

- 增加：符号链接接口 `bucket.put_symlink`，`bucket.get_symlink`


Version 2.2.3
-------------

- 修复：`bucket.resumable_upload` 的返回值从null修正为PutObjectResult
- 修复：优化 `Response.read` 的字符串拼接方式，提高 `bucket.get_object` 的效率 issue #39
- 修复：`bucket.copy_object` 对source key进行url编码


Version 2.2.2
-------------

- 修复：upload_part接口加上headers参数


Version 2.2.1
-------------

- 修复：只有当OSS返回x-oss-hash-crc64ecma头部时，才对上传的文件进行CRC64完整性校验。


Version 2.2.0
-------------

- 依赖：增加新的依赖： `crcmod`
- 增加：上传、下载增加了CRC64校验，缺省打开
- 增加：`RTMP` 直播推流相关接口
- 增加：`bucket.get_object_meta()` 接口，用来更为快速的获取文件基本信息
- 修复：`bucket.object_exists()` 接口采用 `bucket.get_object_meta()` 来实现，避免因镜像回源造成的 issue #39

Version 2.1.1
-------------

- 修复：issue #28。
- 修复：正确的设置连接池大小。


Version 2.1.0
-------------

- 增加：可以通过 `oss2.defaults.connection_pool_size` 来设置连接池的最大连接数。
- 增加：可以通过 `oss2.resumable_upload` 函数的 `num_threads` 参数指定并发的线程数，来进行并发上传。
- 增加：提供断点下载函数 `oss2.resumable_download` 。
- 修复：保存断点信息的文件名应该由“规则化”的本地文件名生成；当断点信息文件格式不是json时，删除断点信息文件。
- 修复：修复一些文档的Bug。

Version 2.0.6
-------------

- 增加：可以通过新增的 `StsAuth` 类，进行STS临时授权
- 增加：加入Travis CI的支持
- 改变：对unit test进行了初步的梳理；

Version 2.0.5
-------------

- 改变：缺省的connect timeout由10秒改为60秒。为了兼容老的requests库（版本低于2.4.0），目前connect timeout和read timeout是同一个值，为了避免
CopyObject、UploadPartCopy因read timeout超时，故把这个超时时间设长。
- 增加：把 `security-token` 加入到子资源中，参与签名。
- 修复：用户可以通过设置oss2.defaults里的变量值，直接修改缺省参数

Version 2.0.4
-------------

- 改变：增加了unittest目录，原先的tests作为functional test；Tox默认是跑unittest
- 修复：按照依赖明确排除requests 2.9.0。因为 `Issue 2844 <https://github.com/kennethreitz/requests/issues/2844>`_ 导致不能传输UTF-8数据。
- 修复：Object名以'/'开头时，oss server应该报InvalidObjectName，而不是报SignatureDoesNotMatch。原因是URL中对'/'也要做URL编码。
- 修复：MANIFEST.in中改正README.rst等



Version 2.0.3
-------------

- 重新设计Python SDK，不再基于原有的官方0.x.x版本开发。
- 只支持Python2.6及以上版本，支持Python 3。
- 基于requests库
