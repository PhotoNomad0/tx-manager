from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.handler import Handler
from libraries.linters.linter_handler import LinterHandler
from libraries.resource_container.ResourceContainer import RC

class RunLinterHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Get all params, both POST and GET and JSON from the request event
        data = {}
        if 'data' in event and isinstance(event['data'], dict):
            data = event['data']
        if 'body-json' in event and event['body-json'] and isinstance(event['body-json'], dict):
            data.update(event['body-json'])
        # Set required env_vars
        args = {
            'source': self.retrieve(data, 'source_url', 'payload'),
            'commit_data': self.retrieve(data, 'commit_data', 'payload', required=False),
            'rc': RC(manifest=self.retrieve(data, 'rc', 'payload', required=False)),
            'prefix': self.retrieve(event['vars'], 'prefix', 'Environment Vars', required=False, default=''),
        }
        linter_class = LinterHandler(**args).get_linter_class()
        return linter_class(**args).run()
        # source = self.retrieve(data, 'source_url', 'payload')
        # resource = self.retrieve(data, 'resource_type', 'payload', required=False)
        # file_type = self.retrieve(data, 'file_type', 'payload', required=False)
        # job_id = self.retrieve(data, 'job_id', 'payload', required=False)
        # messaging_name = self.retrieve(data, 'linter_messaging_name', 'payload', required=False)
        # ret_value = TxManager(**env_vars).run_linter(source, resource, file_type, job_id)
        # if messaging_name:
        #     message_queue = LinterMessaging(messaging_name)
        #     message_queue.notify_lint_job_complete(source, ret_value['success'], payload=ret_value)
        #
        # return ret_value
