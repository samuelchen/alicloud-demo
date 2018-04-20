#!/usr/bin/env python
# coding: utf-8
import logging
import json
from aliyunsdkecs.request.v20140526 import (
    DescribeInstancesRequest,
)
from aliyunsdkcore.client import AcsClient

log = logging.getLogger(__name__)


# CloudWatch and SNS definitions:
BackupLogGroup = 'BackupLogs'
BackupMessageStream = 'BackupLogMessages'
BackupSNSTopic = 'BackupMessageTopic'

# Message Types:
InformationMessage = 'Information'
WarningMessage = 'Warning'
ErrorMessage = 'Error'

optionalTag = None
accountId = '123456789'

MAKE_SNAPSHOT_TIME_SECONDS = 100

prefix = 'Snapshot-Schedule-'
scheduleDict = {}


def handler(event, context):
    log.info('hello world')

    log.info('%s  %s  %s' % (context.region, context.credentials.access_key_id, context.credentials.access_key_secret))

    parms = json.loads(event)
    cred = parms.get('credentials', {})
    access_key = cred.get('access_key_id')
    access_key_secret = cred.get('access_key_secret')

    client = AcsClient(access_key, access_key_secret, context.region)

    request = DescribeInstancesRequest.DescribeInstancesRequest()
    request.set_action_name('DescribeInstances')
    response = client.do_action_with_exception(request)
    vms = json.loads(response.decode())
    return vms


def get_schedulers():
