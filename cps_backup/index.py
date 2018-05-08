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
from aliyunsdkcore.client import AcsClient
import fc2
from fake import fake_context

if __name__ == '__main__':
    from alicloud.settings_dev import ACCESS_KEY, ACCESS_KEY_SECRET
else:
    from ..settings_dev import ACCESS_KEY, ACCESS_KEY_SECRET


log = logging.getLogger(__name__)


# CloudWatch and SNS definitions:
# BackupTag = 'Backup'
BackupLogGroup = 'BackupLogs'
BackupMessageStream = 'BackupLogMessages'
BackupSNSTopic = 'BackupMessageTopic'

# Message Types:
InformationMessage = 'Information'
WarningMessage = 'Warning'
ErrorMessage = 'Error'

accountId = '123456789'

MAKE_SNAPSHOT_TIME_SECONDS = 100

# prefix = 'Snapshot-Schedule-'
scheduleDict = {}


def handler(event, context):
    log.info('hello world')

    log.info('%s  %s  %s' % (context.region, context.credentials.access_key_id, context.credentials.access_key_secret))

    # cred = parms.get('credentials', {})
    # access_key = cred.get('access_key_id')
    # access_key_secret = cred.get('access_key_secret')

    parms = json.loads(event)
    event_name = parms.get('resources')
    optional_tag = parms.get('BackupSchedule')

    backup_handler = BackupHandler(optional_tag=optional_tag)

    if event_name == 'Create':
        print('Snapshot Create Event Fired')
        backup_handler.create_backups()
        # callback('SNAPSHOT CREATION INITIATED')
    elif event_name == 'Delete':
        print('Snapshot Delete Event Fired')
        pass
    else:
        print('LAMBDA WAS NOT CALLED FROM CREATE OR DELETE CRON')


class BackupHandler(object):

    def __init__(self, optional_tag='Default', schedule_prefix='Snapshot-Schedule-'):
        self._service_name = 'test'
        self._func_nam = 'test1'
        self._asc_client = AcsClient(ACCESS_KEY, ACCESS_KEY_SECRET)

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
                # print(vm)
                print('checking instance ', vm['InstanceId'])
                inst_id = vm['InstanceId']
                instance = vm

                shall_backup_instance = False
                is_backup_tagged = False

                schedule_tag = 'Default'
                delete_on = None

                if 'Tags' in instance:
                    for tag in instance['Tags']['Tag']:
                        print(tag['TagKey'], tag['TagValue'])
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
                if not trigger:
                    print('Instance (%s) has unknown backup schedule tag %s.' % (inst_id, schedule_tag))
                    if not self.optional_tag or self.optional_tag == 'Default':
                        print('Performing default backup of instance (%s) for missing schedule %s' % (inst_id, schedule_tag))
                        shall_backup_instance = True

                if shall_backup_instance:
                    disks = self.get_disks(inst_id)
                    print(disks)
                    for d in disks['Disks']['Disk']:
                        vol_id = d['DiskId']
                        volume_list.append(d)
                        instances_dict[vol_id] = (instance, delete_on)

        if len(volume_list) == 0:
            print('No instance found for backup.')
            return

        for vol in volume_list:
            instance, delete_on = instances_dict.get(vol['DiskId'])
            self.make_snapshot(vol, instance, delete_on)


    def make_snapshot(self, vol, instance, delete_on):
        snapshot = self.create_snapshot(vol['DiskId'])
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
        print(rc)

    def get_schedulers(self):

        client = fc2.Client(
            endpoint='%s.cn-hangzhou.fc.aliyuncs.com' % '1563557888557255',
            accessKeyID=ACCESS_KEY,
            accessKeySecret=ACCESS_KEY_SECRET
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

    def get_instances(self):
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_action_name('DescribeInstances')
        response = self.asc_client.do_action_with_exception(request)
        vms = json.loads(response.decode())
        return vms

    def get_tags(self, instance_id):

        request = DescribeTagsRequest.DescribeTagsRequest()
        request.set_action_name('DescribeTags')
        request.set_ResourceId(instance_id)
        request.set_ResourceType('instance')
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
        response = self.asc_client.do_action_with_exception(request)
        snapshot = json.loads(response.decode())
        return snapshot

    def add_tags(self, res_type, res_id, **tag_vals):
        l = len(tag_vals)
        if l == 0:
            return None

        if l > 10:
            print('Support max to 10 tags per resource')
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



if __name__ == '__main__':

    context = fake_context()
    event = json.dumps({'resources': 'Create', 'BackupSchedule': 'daily'})

    handler(event, context)