#!/usr/bin/env python
# coding: utf-8


my_account = Account(endpoint, accid, acckey, token)
queue_name = sys.argv[1] if len(sys.argv) > 1 else "MySampleQueue"
my_queue = my_account.get_queue(queue_name)
#you can get more information of QueueMeta from mns/queue.py
queue_meta = QueueMeta()
try:
    queue_url = my_queue.create(queue_meta)
    print "Create Queue Succeed! QueueName:%s\n" % queue_name
except MNSExceptionBase, e:
    if e.type == "QueueAlreadyExist":
        print "Queue already exist, please delete it before creating or use it directly."
        sys.exit(0)
    print "Create Queue Fail! Exception:%s\n" % e