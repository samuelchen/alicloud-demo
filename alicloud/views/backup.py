#!/usr/bin/evn python

import logging
from django.conf import settings
from django.views.generic import TemplateView
from ..wrapper.common import (
    list_regions,
    list_zones,
    list_images,
    create_secur_group,
    assign_rule_to_secur_group,
)
from ..wrapper.ecs import (
    create_vm,
    list_vms,
    start_vm,
    stop_vm,
    reboot_vm,
    del_vm,
    tag_vm,
)
from cps_backup.index import BackupHandler

log = logging.getLogger(__name__)


class BackupView(TemplateView):

    def get(self, request, *args, **kwargs):
        return super(BackupView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        region = self.request.POST.get('region')
        zone = self.request.POST.get('zone')
        flavor = self.request.POST.get('flavor')
        image = self.request.POST.get('image')
        action = self.request.POST.get('action')
        kw_args = self.request.POST.get('kwargs')
        r = None
        if action:
            tmp = action.split()
            action = tmp[0]
            args = tmp[1:]
            if action == 'create':
                r = create_secur_group(region)
                secur_group = r['SecurityGroupId']
                if secur_group:
                    assign_rule_to_secur_group(region, secur_group, 'tcp', '80/80', '0.0.0.0/0')
                r = create_vm('cps_vm1', region, zone, flavor, image, secur_group=secur_group)
            elif action == 'start':
                r = start_vm(*args)
            elif action == 'stop':
                r = stop_vm(*args)
            elif action == 'reboot':
                r = reboot_vm(*args)
            elif action == 'delete':
                r = del_vm(*args)
            elif action == 'tag':
                tags = {}
                for kv in kw_args.split(','):
                    if kv:
                        k, v = kv.split('=')
                        tags[k.strip()] = v.strip()
                r = tag_vm(*args, **tags)
            elif action == 'refresh':
                pass

        if r:
            log.debug(r)
        return super(BackupView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BackupView, self).get_context_data(**kwargs)
        region = self.get_request_field('region')
        zone = self.get_request_field('zone')

        regions = list_regions()
        context['regions'] = regions
        if not region:
            region = regions['Regions']['Region'][0]['RegionId']

        backup_handler = BackupHandler()
        schedules = backup_handler.get_schedulers()

        vms = list_vms(region)
        for vm in vms['Instances']['Instance']:
            tags = {}
            for t in vm['Tags']['Tag']:
                k = t['TagKey']
                v = t['TagValue']
                tags[t['TagKey']] = t['TagValue']

            if not tags:
                tags = {'Backup': False, 'BackupSchedule': 'Default'}
            vm['tags'] = tags
        context['vms'] = vms

        if region:
            zones = list_zones(region)
            context['zones'] = zones
            if not zone:
                zone = zones['Zones']['Zone'][0]['ZoneId']

            for z in zones['Zones']['Zone']:
                if z['ZoneId'] == zone:
                    context['flavors'] = sorted(z['AvailableInstanceTypes']['InstanceTypes'])

        return context

    def get_request_field(self, name, default=None):
        # return self.request.POST.get(name, self.request.GET.get(name, default))
        return self.request.POST.get(name, default)