# -*- coding: utf-8 -*-

import abc
import time
import requests
import json
import logging
from .exceptions import ClientError
from .utils import to_unixtime
from .compat import to_unicode

logger = logging.getLogger(__name__)


class Credentials(object):
    def __init__(self, access_key_id="", secret_access_key="", security_token=""):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.security_token = security_token

    def get_access_key_id(self):
        return self.access_key_id

    def get_secret_access_key(self):
        return self.secret_access_key

    def get_security_token(self):
        return self.security_token


class EcsRamRoleCredential(Credentials):
    def __init__(self,
                 access_key_id,
                 secret_access_key,
                 security_token,
                 expiration):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.security_token = security_token
        self.expiration = expiration

    def get_access_key_id(self):
        return self.access_key_id

    def get_secret_access_key(self):
        return self.secret_access_key

    def get_security_token(self):
        return self.security_token

    def will_soon_expire(self):
        return int(time.mktime(time.localtime())) >= (self.expiration - 180)


class CredentialsProvider(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_credentials(self):
        return


class StaticCredentialsProvider(CredentialsProvider):
    def __init__(self, access_key_id="", secret_access_key="", security_token=""):
        self.credentials = Credentials(access_key_id, secret_access_key, security_token)

    def get_credentials(self):
        return self.credentials


class EcsRamRoleCredentialsProvider(CredentialsProvider):
    def __init__(self, auth_host, max_retries=3, timeout=10):
        self.fetcher = EcsRamRoleCredentialsFetcher(auth_host)
        self.max_retries = max_retries
        self.timeout = timeout
        self.credentials = None

    def get_credentials(self):
        if self.credentials is None or self.credentials.will_soon_expire():
            try:
                self.credentials = self.fetcher.fetch(self.max_retries, self.timeout)
            except ClientError as e:
                logger.error("Exception: {0}".format(e))
                return None
        return self.credentials


class EcsRamRoleCredentialsFetcher(object):
    def __init__(self, auth_host):
        self.auth_host = auth_host

    def fetch(self, retry_times=3, timeout=10):
        for i in range(0, retry_times):
            try:
                response = requests.get(self.auth_host, timeout=timeout)
                if response.status_code != 200:
                    raise ClientError(
                        "Failed to fetch credentials url, http code:{0}, msg:{1}".format(response.status_code,
                                                                                         response.text))
                dic = json.loads(to_unicode(response.content))
                code = dic.get('Code')
                access_key_id = dic.get('AccessKeyId')
                access_key_secret = dic.get('AccessKeySecret')
                security_token = dic.get('SecurityToken')
                expiration_date = dic.get('Expiration')

                if code != "Success":
                    raise ClientError("Get credentials from ECS metadata service error, code: {0}".format(code))

                expiration_stamp = to_unixtime(expiration_date, "%Y-%m-%dT%H:%M:%SZ")
                return EcsRamRoleCredential(access_key_id, access_key_secret, security_token, expiration_stamp)
            except Exception as e:
                if i == retry_times - 1:
                    logger.error("Exception: {0}".format(e))
                    raise ClientError("Failed to get credentials from ECS metadata service. {0}".format(e))
