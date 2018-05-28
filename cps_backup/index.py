#!/usr/bin/env python
# coding: utf-8
import logging
from datetime import datetime, timezone, timedelta
import time
import json
from aliyunsdkecs.request.v20140526 import (
    DescribeInstancesRequest,
    DescribeTagsRequest,
    DescribeDisksRequest,
    CreateSnapshotRequest,
    AddTagsRequest,
    DescribeSnapshotsRequest,
    DeleteSnapshotRequest,
)
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore import acs_exception
import fc2

from aliyun.log.logitem import LogItem
from aliyun.log.logclient import LogClient
from aliyun.log.putlogsrequest import PutLogsRequest

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)-8s [%(asctime)s] %(name)-30s [%(lineno)d] %(message)s')
# log = logging.getLogger(__name__)
log = None

# CloudWatch and SNS definitions:
# BackupTag = 'Backup'
BackupLogGroup = 'BackupLogs'
BackupMessageStream = 'BackupLogMessages'
BackupSNSTopic = 'BackupMessageTopic'

# Message Types:
InformationMessage = 'Information'
WarningMessage = 'Warning'
ErrorMessage = 'Error'

# accountId = '123456789'

MAKE_SNAPSHOT_TIME_SECONDS = 100

# prefix = 'Snapshot-Schedule-'
# scheduleDict = {}


def handler(event, context):

    # log.info('%s  %s  %s' % (context.region, context.credentials.access_key_id, context.credentials.access_key_secret))

    parms = json.loads(event)
    event_name = parms.get('resources')
    optional_tag = parms.get('BackupSchedule')

    cred = parms.get('credentials', {})
    access_key = cred.get('access_key_id')
    access_key_secret = cred.get('access_key_secret')
    if not cred or not access_key or not access_key_secret:
        cred = context.credentials
        access_key = cred.access_key_id
        access_key_secret = cred.access_key_secret

    global log
    log = AliYunLogService(access_key, access_key_secret, region='cn-hangzhou')
    log.info('CPS Backup service triggered.')

    backup_handler = BackupHandler(optional_tag=optional_tag, region='cn-hangzhou',
                                   access_key=access_key, access_key_secret=access_key_secret)

    if event_name == 'Create':
        log.info('Snapshot Create Event Fired')
        backup_handler.create_backups()
        # callback('SNAPSHOT CREATION INITIATED')
        log.info('Snapshot Creation finished.')
    elif event_name == 'Delete':
        log.info('Snapshot Delete Event Fired')
        backup_handler.delete_backups()
    else:
        log.info('LAMBDA WAS NOT CALLED FROM CREATE OR DELETE CRON')


class BackupHandler(object):

    def __init__(self, optional_tag='Default', schedule_prefix='Snapshot-Schedule-',
                 region='cn-hangzhou', access_key=None, access_key_secret=None):
        self._service_name = 'test'
        self._func_nam = 'test1'
        self._account_id = '1563557888557255'
        self._region = region
        self._access_key = access_key
        self._access_key_secret = access_key_secret
        self._asc_client = AcsClient(self._access_key, self._access_key_secret, self._region)

        self._schedule_tag = 'BackupSchedule'
        self._backup_tag = 'Backup'
        self._delete_period_tag = 'RetentionPeriod'
        self._optional_tag = optional_tag
        self._schedule_prefix = schedule_prefix

        self._schedule_dict = None


    @property
    def service_name(self):
        return self._service_name

    @property
    def function_name(self):
        return self._func_nam

    @property
    def asc_client(self):
        return self._asc_client

    @property
    def backup_tag(self):
        return self._backup_tag

    @property
    def schedule_tag(self):
        return self._schedule_tag

    @property
    def delete_period_tag(self):
        return self._delete_period_tag

    @property
    def optional_tag(self):
        return self._optional_tag

    @property
    def schedule_prefix(self):
        return self._schedule_prefix

    @property
    def schedule_dict(self):
        if not self._schedule_dict:
            self._schedule_dict = self.get_schedulers()
        return self._schedule_dict

    def create_backups(self):
        volume_list = []
        instances_dict = {}
        vms = self.get_instances()

        if 'Instances' in vms:
            for vm in vms['Instances']['Instance']:
                # log.info(vm)
                log.info('checking tags of instance %s' % vm['InstanceId'])
                inst_id = vm['InstanceId']
                instance = vm

                shall_backup_instance = False
                is_backup_tagged = False

                schedule_tag = 'Default'
                delete_on = None

                if 'Tags' in instance:
                    for tag in instance['Tags']['Tag']:
                        log.info('\t %s = %s' % (tag['TagKey'], tag['TagValue']))
                        key = tag.get('TagKey')
                        val = tag.get('TagValue')

                        if key and key.lower() == self.backup_tag.lower():
                            if val and val.lower() == 'true':
                                is_backup_tagged = True
                        elif key and key.lower() == self.schedule_tag.lower():
                            if val:
                                schedule_tag = val
                        elif key and key.lower() == self.delete_period_tag.lower():
                            if val:
                                days = int(val)
                                delete_on = datetime.utcnow() + timedelta(days=days)

                if not is_backup_tagged:
                    continue

                if self.optional_tag and self.optional_tag != 'Default':
                    if schedule_tag == self.optional_tag:
                        shall_backup_instance = True
                elif schedule_tag == 'Default':
                    shall_backup_instance = True

                trigger = self.schedule_dict.get(schedule_tag)
                # log.info(trigger)
                if not trigger:
                    log.info('Instance (%s) has unknown backup schedule tag %s.' % (inst_id, schedule_tag))
                    if not self.optional_tag or self.optional_tag == 'Default':
                        log.info('Performing default backup of instance (%s) for missing schedule %s' % (inst_id, schedule_tag))
                        shall_backup_instance = True

                if shall_backup_instance:
                    disks = self.get_disks(inst_id)
                    # log.info(disks)
                    for d in disks['Disks']['Disk']:
                        vol_id = d['DiskId']
                        volume_list.append(d)
                        instances_dict[vol_id] = (instance, delete_on)

        if len(volume_list) == 0:
            log.info('No instance volumes found for backup.')
            return

        for vol in volume_list:
            instance, delete_on = instances_dict.get(vol['DiskId'])
            log.info('\t make snapshot for instance %s disk %s' % (instance['InstanceId'], vol['DiskId']))
            self.make_snapshot(vol, instance, delete_on)

    def delete_backups(self):
        snapshots = self.list_snapshots()
        if 'Snapshots' in snapshots:
            for s in snapshots['Snapshots']['Snapshot']:
                if 'Tags' in s:
                    for t in s['Tags']['Tag']:
                        k = t['TagKey']
                        v = t['TagValue']
                        if k == self.delete_period_tag:
                            delete_on = datetime.strftime(v)
                            log.info('Backup delete on %s' % delete_on)
                            if delete_on <= datetime.utcnow():
                                self.del_snapshots(s['SnapshotId'])

    def make_snapshot(self, vol, instance, delete_on):
        snapshot = self.create_snapshot(vol['DiskId'])
        if snapshot is not None:
            snapshot_id = snapshot['SnapshotId']
            self.tag_snapshots(snapshot_id, instance, delete_on, vol)

    def tag_snapshots(self, snapshot_id, instance, delete_on, vol):
        snapshot_tags = ['Application', 'Compliance', 'Department', 'Environment',
                         'InstanceName', 'MountPoint', 'Project', 'Owner']

        instance_tags = instance['Tags']['Tag']
        vol_tags = vol['Tags']['Tag']
        new_tags = []
        new_tags.extend(instance_tags)
        new_tags.extend(vol_tags)

        keep_tags = {}

        for tag in new_tags:
            key = tag['TagKey']

            # check for tags keep
            for stag in snapshot_tags:
                if key.startswith(stag):
                    keep_tags[tag['TagKey']] = tag['TagValue']

        if delete_on:
            keep_tags[self.delete_period_tag] = str(delete_on)

        keep_tags['Name'] = 'InstanceId: ' + instance['InstanceId']
        # volume name tag:  <Instance-Name-Tag>-<Volume-Device>
        instance_name = 'Instance'
        for tag in instance_tags:
            if tag['TagKey'] == 'Name':
                instance_name = tag['TagValue']
        keep_tags['VolumeName'] = instance_name + '-' + vol['Device']

        rc = self.add_tags('snapshot', snapshot_id, **keep_tags)
        # log.info(rc)
        return rc

    def get_schedulers(self):

        client = fc2.Client(
            endpoint='%s.%s.fc.aliyuncs.com' % (self._account_id, self._region),
            accessKeyID=self._access_key,
            accessKeySecret=self._access_key_secret
        )

        triggers = client.list_triggers(serviceName=self.service_name, functionName=self.function_name)
        if triggers:
            triggers = triggers.data

        rc = {}
        for t in triggers['triggers']:
            if 'enable' in t['triggerConfig'] and t['triggerConfig']['enable']:
                name = t['triggerName']
                if not name.startswith(self.schedule_prefix):
                    continue
                name.replace(self.schedule_prefix, '')
                rc[name] = t
        rc['Default'] = 24
        return rc

    def get_instances(self):
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_action_name('DescribeInstances')
        response = self.asc_client.do_action_with_exception(request)
        vms = json.loads(response.decode())
        return vms

    def get_tags(self, res_type, res_id):

        request = DescribeTagsRequest.DescribeTagsRequest()
        request.set_action_name('DescribeTags')
        request.set_ResourceId(res_id)
        request.set_ResourceType(res_type)
        response = self.asc_client.do_action_with_exception(request)
        tags = json.loads(response.decode())
        return tags

    def get_disks(self, instance_id):

        request = DescribeDisksRequest.DescribeDisksRequest()
        request.set_action_name('DescribeDisks')
        request.set_InstanceId(instance_id)
        response = self.asc_client.do_action_with_exception(request)
        disks = json.loads(response.decode())
        return disks

    def create_snapshot(self, disk_id):
        request = CreateSnapshotRequest.CreateSnapshotRequest()
        request.set_action_name('CreateSnapshot')
        request.set_DiskId(disk_id)
        try:
            response = self.asc_client.do_action_with_exception(request)
        except acs_exception.exceptions.ServerException as err:
            log.error('\t Fail to create snapshot: %s' % str(err))
            return None
        snapshot = json.loads(response.decode())
        log.info('\t Snapshot created for disk %s' % disk_id)
        return snapshot

    def add_tags(self, res_type, res_id, **tag_vals):
        l = len(tag_vals)
        if l == 0:
            return None

        if l > 10:
            log.info('Support max to 10 tags per resource')
            return None

        rc = []
        i = 1
        is_submited = False
        if tag_vals:
            for tag, val in tag_vals.items():
                if (i-1) % 5 == 0:
                    request = AddTagsRequest.AddTagsRequest()
                    request.set_action_name('AddTags')
                    request.set_ResourceType(res_type)
                    request.set_ResourceId(res_id)
                    is_submited = False

                key_name = 'Tag.%d.Key' % i
                val_name = 'Tag.%d.Value' % i

                request.add_query_param(key_name, tag)
                request.add_query_param(val_name, val)

                i += 1

                if (i-1) % 5 == 0:
                    response = self.asc_client.do_action_with_exception(request)
                    rc.append(json.loads(response.decode()))
                    is_submited = True
                    i = 1

        if not is_submited:
            response = self.asc_client.do_action_with_exception(request)
            rc.append(json.loads(response.decode()))

        return rc

    def list_snapshots(self, ids=None):
        # client = create_acs_client(region=self._region)

        request = DescribeSnapshotsRequest.DescribeSnapshotsRequest()
        request.set_action_name('DescribeSnapshots')
        # request.add_query_param('RegionId', region)
        request.add_query_param('PageSize', 100)
        response = self.asc_client.do_action_with_exception(request)
        r = json.loads(response.decode())
        log.debug(r)
        return r

    def del_snapshots(self, snapshot_id):
        # client = create_acs_client(region=self._region)

        request = DeleteSnapshotRequest.DeleteSnapshotRequest()
        request.set_action_name('DeleteSnapshot')
        request.set_SnapshotId(snapshot_id)
        # request.add_query_param('RegionId', region)
        response = self.asc_client.do_action_with_exception(request)
        r = json.loads(response.decode())
        log.debug(r)
        return r


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
        self._pylog = logging.getLogger(__name__)

    def log(self, contents, topic, source):
        level = int(getattr(logging, topic))
        self._pylog.log(level=level, msg=contents)

        contents = [('msg', contents), ]
        logitemList = []
        logItem = LogItem()
        logItem.set_time(int(time.time()))
        logItem.set_contents(contents)
        logitemList.append(logItem)
        req = PutLogsRequest(self._project, self._logstore, topic, source, logitemList)
        resp = self._client.put_logs(req)
        return resp

    def debug(self, contents, source='BackupLogs'):
        self.log(contents, topic='DEBUG', source=source)

    def info(self, contents, source='BackupLogs'):
        self.log(contents, topic='INFO', source=source)

    def warn(self, contents, source='BackupLogs'):
        self.log(contents, topic='WARN', source=source)

    def error(self, contents, source='BackupLogs'):
        self.log(contents, topic='ERROR', source=source)


if __name__ == '__main__':
    from cps_backup.fake import fake_context
    # log = AliYunLogService(access_key, access_key_secret, region='cn-hangzhou')
    # log.info('CPS Backup service triggered.')
    context = fake_context()
    event = json.dumps({'resources': 'Create', 'BackupSchedule': 'Default'})

    handler(event, context)