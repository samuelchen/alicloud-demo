#!/usr/bin/env python
# coding: utf-8

import oss2
from django.conf import settings
import logging
import json

log = logging.getLogger(__name__)


class OSS(object):

    def __init__(self, region=settings.DEFAULT_REGION,
                 access_key=settings.ACCESS_KEY,
                 access_key_secret=settings.ACCESS_KEY_SECRET,
                 is_https=False):
        self._region = region
        self._access_key = access_key
        self._access_key_secret = access_key_secret
        self._is_https = is_https
        self._endpoint = self.get_endpoint(self._is_https)

        self._auth = oss2.Auth(settings.ACCESS_KEY, settings.ACCESS_KEY_SECRET)

    @property
    def endpoint(self):
        return self._endpoint

    def get_endpoint(self, is_https=False):
        if is_https:
            return 'https://oss-%s.aliyuncs.com' % self._region
        else:
            return 'http://oss-%s.aliyuncs.com' % self._region

    def list_buckets(self):
        r = None
        e = None
        try:
            service = oss2.Service(self._auth, self.endpoint)
            # r = oss2.BucketIterator(service)
            r = [b.name for b in oss2.BucketIterator(service)]
        except oss2.exceptions.ServerError as err:
            e = json.loads(str(err).replace("'", '"'))
        log.debug(r or e)
        return r, e

    def get_bucket(self, name):
        r = None
        e = None
        try:
            r = oss2.Bucket(self._auth, self.endpoint, name)
        except oss2.exceptions.ServerError as err:
            e = json.loads(str(err).replace("'", '"'))
        log.debug(r or e)
        return r, e

    def create_bucket(self, name):
        r = None
        e = None
        try:
            bucket, e = self.get_bucket(name)
            r = bucket.create_bucket()
        except oss2.exceptions.ServerError as err:
            e = json.loads(str(err).replace("'", '"'))
        log.debug(r or e)
        return r, e

    def delete_bucket(self, name):

        r = None
        e = None
        try:
            bucket, e = self.get_bucket(name)
            if bucket:
                r = bucket.delete_bucket()
        except oss2.exceptions.ServerError as err:
            e = json.loads(str(err).replace("'", '"'))
        log.debug(r or e)
        return r, e

    def put_object(self, bucket, key, obj):
        r = None
        e = None
        try:
            headers = {'Content-Type': 'text/plain; charset=utf-8'}     # for demo
            r = bucket.put_object(key, obj, headers=headers)
        except oss2.exceptions.ServerError as err:
            e = json.loads(str(err).replace("'", '"'))
        log.debug(r or e)
        return r, e

    def get_object(self, bucket, key):
        r = None
        e = None
        try:
            r = bucket.get_object(key)
        except oss2.exceptions.ServerError as err:
            e = json.loads(str(err).replace("'", '"'))
        log.debug(r or e)
        return r, e

    def gen_object_url(self, bucket, key, expires=60):
        r = None
        e = None
        try:
            r = bucket.sign_url('GET', key, expires)
        except oss2.exceptions.ServerError as err:
            e = json.loads(str(err).replace("'", '"'))
        log.debug(r or e)
        return r, e

    def list_objects(self, bucket):
        r = []
        e = None
        try:
            # r = oss2.ObjectIterator(bucket)
            for o in oss2.ObjectIterator(bucket):
                url, e = self.gen_object_url(bucket, o.key, 300)
                if e: print(e)
                r.append({'key': o.key, 'url': url})
        except oss2.exceptions.ServerError as err:
            e = json.loads(str(err).replace("'", '"'))
        log.debug(r or e)
        return r, e

    def delete_object(self, bucket, key):
        r = None
        e = None
        try:
            r = bucket.delete_object(key)
        except oss2.exceptions.ServerError as err:
            e = json.loads(str(err).replace("'", '"'))
        log.debug(r or e)
        return r, e

    def exist_object(self, bucket, key):
        r = None
        e = None
        try:
            r = bucket.exist_object(key)
        except oss2.exceptions.ServerError as err:
            e = json.loads(str(err).replace("'", '"'))
        log.debug(r or e)
        return r, e