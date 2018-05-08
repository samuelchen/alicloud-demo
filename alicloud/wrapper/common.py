#!/usr/bin/env python
# coding: utf-8

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526 import (
    DescribeRegionsRequest,
    DescribeZonesRequest,
    DescribeImagesRequest,
    CreateSecurityGroupRequest,
    AuthorizeSecurityGroupRequest,
)
import logging
import json
from django.core.cache import cache
from django.conf import settings

log = logging.getLogger(__name__)



def create_acs_client(region=settings.DEFAULT_REGION):
    return AcsClient(
        settings.ACCESS_KEY,
        settings.ACCESS_KEY_SECRET,
        region
    )


def list_regions():

    cache_key = 'list_regions'
    r = cache.get(cache_key)
    if r is None:
        client = create_acs_client()

        request = DescribeRegionsRequest.DescribeRegionsRequest()
        request.set_action_name('DescribeRegions')
        response = client.do_action_with_exception(request)
        r = json.loads(response.decode())
        log.debug(r)
        cache.set(cache_key, r)
    return r


def list_zones(region):

    cache_key = 'list_zones_%s' % region
    r = cache.get(cache_key)
    if r is None:
        client = create_acs_client(region=region)

        request = DescribeZonesRequest.DescribeZonesRequest()
        request.set_action_name('DescribeZones')
        request.add_query_param('RegionId', region)
        response = client.do_action_with_exception(request)
        r = json.loads(response.decode())
        log.debug(r)
        cache.set(cache_key, r)
    return r


def list_images(region):

    cache_key = 'list_images_%s' % region
    r = cache.get(cache_key)
    if r is None:
        client = create_acs_client(region=region)

        request = DescribeImagesRequest.DescribeImagesRequest()
        request.set_action_name('DescribeImages')
        request.add_query_param('RegionId', region)
        request.set_PageSize(50)
        response = client.do_action_with_exception(request)
        r = json.loads(response.decode())
        log.debug(r)
        cache.set(cache_key, r, 300)
    return r


def create_secur_group(region, vpcid=None):

    client = create_acs_client(region=region)

    request = CreateSecurityGroupRequest.CreateSecurityGroupRequest()
    request.set_action_name('CreateSecurityGroup')
    request.add_query_param('RegionId', region)
    if vpcid:
        request.set_VpcId(vpcid)
    response = client.do_action_with_exception(request)
    r = json.loads(response.decode())
    log.debug(r)
    return r


def assign_rule_to_secur_group(region, sgid, protocol, port_rage, src_cidr_ip):

    client = create_acs_client(region=region)

    request = AuthorizeSecurityGroupRequest.AuthorizeSecurityGroupRequest()
    request.set_action_name('AuthorizeSecurityGroup')
    request.add_query_param('RegionId', region)
    request.set_SecurityGroupId(sgid)
    request.set_IpProtocol(protocol)
    request.set_PortRange(port_rage)
    request.set_SourceCidrIp(src_cidr_ip)
    response = client.do_action_with_exception(request)
    r = json.loads(response.decode())
    log.debug(r)
    return r




