from __future__ import unicode_literals, print_function
from libraries.manager.manager import TxManager
from libraries.lambda_handlers.handler import Handler


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
        env_vars = {
            'job_table_name': self.retrieve(event['vars'], 'job_table_name', 'Environment Vars'),
            'prefix': self.retrieve(event['vars'], 'prefix', 'Environment Vars', required=False, default='')
        }
        source = self.retrieve(data, 'source_url', 'payload')
        resource = self.retrieve(data, 'resource_type', 'payload', required=False)
        file_type = self.retrieve(data, 'file_type', 'payload', required=False)
        job_id = self.retrieve(data, 'job_id', 'payload', required=False)
        return TxManager(**env_vars).run_linter(source, resource, file_type, job_id)
