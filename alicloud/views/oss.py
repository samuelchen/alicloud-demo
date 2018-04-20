#!/usr/bin/evn python

import logging
from django.views.generic import TemplateView
from django.contrib.messages import debug, info, warning, error, constants
from ..wrapper.oss import (
    OSS
)

log = logging.getLogger(__name__)


class OSSView(TemplateView):

    def get(self, request, *args, **kwargs):
        return super(OSSView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        bname = request.POST.get('bucket_sel', None)
        key = request.POST.get('key', None)
        obj = request.POST.get('obj', None)
        key_del = request.POST.get('obj_sel', None)

        oss = OSS()
        if bname:
            bucket, e = oss.get_bucket(bname)
            if e: error(request, e)
        else:
            bname = request.POST.get('bucket', None)
            if bname:
                bucket, e = oss.create_bucket(bname)
                if not e:
                    info(request, 'Bucket %s created.' % bname)
                else:
                    error(request, e)

        if key and obj:
            r, e = oss.put_object(bucket, key, obj)
            if e:
                error(request, e)
            else:
                info(request, 'Object %s saved.' % key)

        elif key_del:
            r, e = oss.delete_object(bucket, key_del)
            if not e:
                info(self.request, 'Object %s deleted' % key_del)
            else:
                error(self.request, e)

        return super(OSSView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OSSView, self).get_context_data(**kwargs)
        bname = self.request.POST.get('bucket_sel', None)

        oss = OSS()
        context['buckets'], e = oss.list_buckets()
        if e: error(self.request, e)

        if bname:
            bucket, e = oss.get_bucket(bname)
            if bucket:
                context['objects'], e = oss.list_objects(bucket)
        return context
