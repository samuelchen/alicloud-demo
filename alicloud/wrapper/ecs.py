#!/usr/bin/env python
# coding: utf-8

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526 import (
    CreateInstanceRequest,
    DescribeInstancesRequest,
    StartInstanceRequest,
    StopInstanceRequest,
    RebootInstanceRequest,
    DeleteInstanceRequest,
    AddTagsRequest,
)
from django.conf import settings
from .common import (
    create_acs_client,
    create_secur_group
)
import json
import logging
from django.core.cache import cache

log = logging.getLogger(__name__)


def create_vm(name, region, zone, flavor, image, secur_group, **kwargs):

    client = create_acs_client(region)

    request = CreateInstanceRequest.CreateInstanceRequest()
    request.add_query_param('RegionId', region)
    request.set_ZoneId(zone)
    request.set_ImageId(image)
    request.set_InstanceName(name)
    request.set_SecurityGroupId(secur_group)
    request.set_InstanceType(flavor)
    for k, v in kwargs.items():
        request.add_query_param(k, v)
    # request.set_ClientToken("<uuid>")

    response = client.do_action_with_exception(request)
    log.debug(response)
    r = json.loads(response.decode())
    return r


def start_vm(vmid):
    client = create_acs_client()

    request = StartInstanceRequest.StartInstanceRequest()
    request.set_action_name('StartInstance')
    request.set_InstanceId(vmid)
    response = client.do_action_with_exception(request)
    r = json.loads(response.decode())
    log.debug(r)
    return r


def stop_vm(vmid):
    client = create_acs_client()

    request = StopInstanceRequest.StopInstanceRequest()
    request.set_action_name('StopInstance')
    request.set_InstanceId(vmid)
    response = client.do_action_with_exception(request)
    r = json.loads(response.decode())
    log.debug(r)
    return r


def reboot_vm(vmid):
    client = create_acs_client()

    request = RebootInstanceRequest.RebootInstanceRequest()
    request.set_action_name('RebootInstance')
    request.set_InstanceId(vmid)
    response = client.do_action_with_exception(request)
    r = json.loads(response.decode())
    log.debug(r)
    return r


def del_vm(vmid):
    client = create_acs_client()

    request = DeleteInstanceRequest.DeleteInstanceRequest()
    request.set_action_name('DeleteInstance')
    request.set_InstanceId(vmid)
    response = client.do_action_with_exception(request)
    r = json.loads(response.decode())
    log.debug(r)
    return r


def list_vms(region, ids=None):
    client = create_acs_client(region=region)

    request = DescribeInstancesRequest.DescribeInstancesRequest()
    request.set_action_name('DescribeInstances')
    # request.add_query_param('RegionId', region)
    response = client.do_action_with_exception(request)
    r = json.loads(response.decode())
    log.debug(r)
    return r


def get_vm(region, vmid):
    return list_vms(region, ids=[vmid, ])


def tag_vm(vm_id, **tag_vals):

    l = len(tag_vals)
    if l == 0:
        return None

    if l > 10:
        print('Support max to 10 tags per resource')
        return None

    asc_client = create_acs_client()

    rc = []
    i = 1
    is_submited = False
    if tag_vals:
        for tag, val in tag_vals.items():
            if (i-1) % 5 == 0:
                request = AddTagsRequest.AddTagsRequest()
                request.set_action_name('AddTags')
                request.set_ResourceType('instance')
                request.set_ResourceId(vm_id)
                is_submited = False

            key_name = 'Tag.%d.Key' % i
            val_name = 'Tag.%d.Value' % i

            request.add_query_param(key_name, tag)
            request.add_query_param(val_name, val)

            i += 1

            if (i-1) % 5 == 0:
                response = asc_client.do_action_with_exception(request)
                rc.append(json.loads(response.decode()))
                is_submited = True
                i = 1

    if not is_submited:
        response = asc_client.do_action_with_exception(request)
        rc.append(json.loads(response.decode()))

    return rc
