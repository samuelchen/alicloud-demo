#!/usr/bin/evn python

import logging
from django.views.generic import TemplateView

log = logging.getLogger(__name__)


class HomeView(TemplateView):

    def get(self, request, *args, **kwargs):
        return super(HomeView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        params = {}
        region = self.request.POST.get('region')
        params["region"] = self.request.POST.get('region')
        zone = self.request.POST.get('zone')
        params["vpc_name"] = self.request.POST.get('vpc_name')
        params["vpc_cidr"] = self.request.POST.get('vpc_cidr')
        params["switch_name"] = self.request.POST.get('switch_name')
        params["switch_cidr"] = self.request.POST.get('switch_cidr')
        params["vm_name"] = self.request.POST.get('vm_name')
        params["vm_ip"] = self.request.POST.get('vm_ip')
        params["vm_image"] = self.request.POST.get('vm_image')
        params["vm_flavor"] = self.request.POST.get('vm_flavor')
        params["security_group"] = self.request.POST.get('security_group')
        params["zone"] = region+"-"+zone
        print (params)

        return super(HomeView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        return context
