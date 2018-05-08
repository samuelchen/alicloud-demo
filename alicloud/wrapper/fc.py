#!/usr/bin/env python
# coding: utf-8
import logging
from datetime import datetime, timezone, timedelta
import json
from aliyunsdkecs.request.v20140526 import (
    DescribeInstancesRequest,
    DescribeTagsRequest,
    DescribeDisksRequest,
    CreateSnapshotRequest,
    AddTagsRequest,
)
from django.conf import settings
from aliyunsdkcore.client import AcsClient
import fc2


def get_schedulers():

    client = fc2.Client(
        endpoint='%s.cn-hangzhou.fc.aliyuncs.com' % '1563557888557255',
        accessKeyID=settings.ACCESS_KEY,
        accessKeySecret=settings.ACCESS_KEY_SECRET
    )

    triggers = client.list_triggers(serviceName=self.service_name, functionName=self.function_name)
    if triggers:
        triggers = triggers.data

    rc = {}
    for t in triggers['triggers']:
        if t['triggerConfig']['enable']:
            name = t['triggerName']
            if not name.startswith(self.schedule_prefix):
                continue
            name.replace(self.schedule_prefix, '')
            rc[name] = t
    rc['Default'] = 24
    return rc