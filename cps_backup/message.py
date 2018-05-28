#!/usr/bin/env python
# coding: utf-8


import time
from aliyun.log.logitem import LogItem
from aliyun.log.logclient import LogClient
from aliyun.log.putlogsrequest import PutLogsRequest


class AliYunLogService(object):

    def __init__(self, access_key, access_key_secret, region='cn-hangzhou',
                 project='log-project-001', logstore='logstore-backup'):
        self._access_key = access_key
        self._access_key_secret = access_key_secret
        self._region = region
        self._project = project
        self._logstore = logstore
        self._endpoint = '%s.log.aliyuncs.com' % self._region
        self._client = LogClient(self._endpoint, self._access_key, self._access_key_secret)

        self._topic = 'BackupLogs'

    def log(self, topic, source, contents):
        logitemList = []
        logItem = LogItem()
        logItem.set_time(int(time.time()))
        logItem.set_contents(contents)
        logitemList.append(logItem)
        req = PutLogsRequest(self._project, self._logstore, topic, source, logitemList)
        resp = self._client.put_logs(req)
        return resp