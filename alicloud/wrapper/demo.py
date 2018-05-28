#!/usr/bin/env python
# coding: utf-8

from ..services.vpc.vpc_service import VpcManager, VSwitch, NATRule
from .ecs import create_vm, create_secur_group, start_vm
from .common import assign_rule_to_secur_group
from django.conf import settings
import logging
import time

log = logging.getLogger(__name__)


def demo(params):
    log.debug('Demo start...')
    vms = [
        {'name': params['vm_name'], 'ip': params['vm_ip']}
    ]
    region = params['region']
    zone = params['zone']
    flavor = params['vm_flavor']
    image = params['vm_image']
    securegroup = params['security_group']

    vpc_name = params['vpc_name']
    vpc_cidr = params['vpc_cidr']
    vswitch_name = params['switch_name']
    vswitch_cidr = params['switch_cidr']

    vswitch_obj = VSwitch()
    vswitch_obj.vswitch_name = vswitch_name
    vswitch_obj.cidr_block = vswitch_cidr
    vswitch_obj.zone_id = zone

    vpc = VpcManager(settings.ACCESS_KEY, settings.ACCESS_KEY_SECRET, region)
    vpc_id, vswitch_id, nat_gateway_id, eip = vpc.create_vpc_all_in_one(vpc_name, vpc_cidr, vswitch_obj)

    sg = create_secur_group(region, vpc_id)
    securegroup = sg['SecurityGroupId']
    if securegroup:
        assign_rule_to_secur_group(region, securegroup, 'tcp', '80/80')

    vmids = []
    for vm in vms:
        r = create_vm(vm['name'], region, zone, flavor, image, securegroup,
                      VSwitchId=vswitch_id, PrivateIpAddress=vm['ip'])
        log.debug(r)

        vmids.append(r['InstanceId'])

    rule1 = NATRule(eip, "any", "TCP", vms[0]['ip'], "any")
    nat_rule_obj_list = [rule1]
    vpc.add_nat_rules(vpc_id, nat_gateway_id, nat_rule_obj_list)

    time.sleep(20)
    for vmid in vmids:
        r = start_vm(vmid)
        log.debug(r)