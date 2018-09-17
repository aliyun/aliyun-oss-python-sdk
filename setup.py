#!/usr/bin/env python

import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


version = ''
with open('oss2/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')


with open('README.rst', 'rb') as f:
    readme = f.read().decode('utf-8')

setup(
    name='oss2',
    version=version,
    description='Aliyun OSS (Object Storage Service) SDK',
    long_description=readme,
    packages=['oss2'],
    install_requires=['requests!=2.9.0',
                      'crcmod>=1.7',
                      'pycryptodome>=3.4.7',
                      'aliyun-python-sdk-kms>=2.4.1',
                      'aliyun-python-sdk-core>=2.6.2' if sys.version_info[0] == 2 else 'aliyun-python-sdk-core-v3>=2.5.5'],
    include_package_data=True,
    url='http://oss.aliyun.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ]
)
