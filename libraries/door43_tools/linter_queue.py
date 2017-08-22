from __future__ import print_function, unicode_literals

from libraries.door43_tools.messaging_service import MessagingService


class LinterQueue(MessagingService):
    def __init__(self, queue_name="linter_complete", region="us-west-2"):
        super(LinterQueue, self).__init__(queue_name, region)

    def clear_lint_jobs(self, source_url, filenames, timeout=5):
        return self.wait_for_lint_jobs(source_url, filenames, timeout)

    def wait_for_lint_jobs(self, source_url, filenames, timeout=5):
        items_to_look_for = []
        for f in filenames:
            id = self.get_id(source_url, f)
            items_to_look_for.append(id)

        return self.wait_for_messages(items_to_look_for, timeout)

    def notify_lint_job_complete(self, source_url, filename, success):
        id = self.get_id(source_url, filename)
        payload = {
            'source_url': source_url,
            'file_name':  filename
        }
        return self.send_message(id, success, payload)

    def get_id(self, source_url, file_name):
        id = source_url + "?file=" + file_name
        return id
