from __future__ import print_function, unicode_literals

import json
import time
import boto.sqs
from boto.sqs.message import Message


class MessagingService(object):

    def __init__(self, queue_name, region="us-west-2"):
        self.queue_name = queue_name
        self.region = region
        self.connection = None
        self.queue = None
        self.recvd_payloads = None

    def get_connection(self):
        if not self.connection:
            self.connection = boto.sqs.connect_to_region(self.region)
        if not self.queue:
            self.queue = self.connection.get_queue(self.queue_name)
        return self.queue

    def send_message(self, item_id, success, payload=None):
        if not self.get_connection():
            return False

        data = {
            'id': item_id,
            'success': success
        }
        if payload:
            if isinstance(payload, basestring):
                data['payload'] = payload
            else:  # treat as dictionary and append data
                for k in payload:
                    data[k] = payload[k]

        m = Message()
        data_json = json.dumps(data, encoding="UTF-8")
        m.set_body(data_json)
        self.queue.write(m)
        return True

    def clear_old_messages(self, items_to_look_for, timeout=5):
        return self.wait_for_messages(items_to_look_for, timeout)

    def wait_for_messages(self, items_to_watch_for, timeout=120):
        if not self.get_connection():
            return False

        start = time.time()
        self.recvd_payloads = {}
        while (len(self.recvd_payloads) < len(items_to_watch_for)) and (int(time.time() - start) < timeout):
            rs = self.queue.get_messages(visibility_timeout=5)
            for m in rs:
                # print(m)
                message_body = m.get_body()
                if message_body:
                    recvd = json.loads(message_body, encoding="UTF-8")
                    if 'id' in recvd:
                        item_id = recvd['id']
                        if item_id in items_to_watch_for:  # if this matches what we were looking for, then remove it
                                                           # from queue
                            self.queue.delete_message(m)
                            self.recvd_payloads[item_id] = recvd
        success = len(self.recvd_payloads) >= len(items_to_watch_for)
        return success
