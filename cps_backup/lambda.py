#!/usr/bin/env python
# coding: utf-8

if __name__ == '__main__':
    from alicloud.settings_dev import ACCESS_KEY, ACCESS_KEY_SECRET
else:
    from ..settings_dev import ACCESS_KEY, ACCESS_KEY_SECRET


class Credentials:
    def __init__(self, access_key_id, access_key_secret, security_token):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.security_token = security_token

    def __str__(self):
        return '<Credentials key_id=%s secret=%s token=%s>' % (self.access_key_id, self.access_key_secret, self.security_token)


class ServiceMeta:
    def __init__(self, service_name, log_project, log_store):
        self.name = service_name
        self.log_project = log_project
        self.log_store = log_store


class FunctionMeta:
    def __init__(self, name, handler, memory, timeout):
        self.name = name
        self.handler = handler
        self.memory = memory
        self.timeout = timeout


class FCContext:
    def __init__(self, account_id, request_id, credentials, function_meta, service_meta, region):
        self.requestId = request_id
        self.credentials = credentials
        self.function = function_meta
        self.request_id = request_id
        self.region = region

    def __str__(self):
        return '<FCContext id=5%s region=%s credentials=%s>' % (self.request_id, self.region, self.credentials)


def fake_context():
    idx = 1

    token = 'fake-token-%04d' % idx
    credentials = Credentials(ACCESS_KEY, ACCESS_KEY_SECRET, token)

    func_name = 'fake-func-name-%04d' % idx
    func_meta = FunctionMeta(func_name, None, None, None)

    svc_name = 'fake-svc-name-%04d' % idx
    svc_meta = ServiceMeta(svc_name, None, None)

    accid = 'fake-user-id-%04d' % idx
    reqid = 'fake-request-id-%04d' % idx
    region = 'cn-hangzhou'
    context = FCContext(accid, reqid, credentials, func_meta, svc_meta, region)

    return context


if __name__ == '__main__':
    context = fake_context()
    print(context)