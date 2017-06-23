from __future__ import print_function, unicode_literals
import logging
import os
import tempfile
import urlparse
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.models.manifest import TxManifest


class ViewCount(object):
    MANIFEST_TABLE_NAME = 'tx-manifest'
    INVALID_URL_ERROR = 'repo not found for: '
    DB_ACCESS_ERROR = 'could not access view counts for: '

    def __init__(self, gogs_user_token=None, manifest_table_name=None):
        """
        :param string gogs_user_token:
        :param string manifest_table_name:
        """
        self.manifest_table_name = manifest_table_name
        self.manifest_db_handler = None
        self.logger = logging.getLogger()

        # move everything down one directory levek for simple delete
        self.intermediate_dir = 'view_count'
        self.base_temp_dir = os.path.join(tempfile.gettempdir(), self.intermediate_dir)

    def get_view_count(self, path, increment=0):
        self.logger.debug("Start: get_view_count")

        response = {  # default to error
            'ErrorMessage': ViewCount.INVALID_URL_ERROR + path
        }

        parsed = urlparse.urlparse(path)
        try:
            empty, u, repo_owner, repo_name = parsed.path.split('/')[0:4]
        except:
            self.logger.warning("Invalid repo url: " + path)
            return response

        if (empty != '') or (u != 'u'):
            self.logger.warning("Invalid repo url: " + path)
            return response

        if not self.manifest_table_name:
            site = ''
            netloc_parts = parsed.netloc.split('-')
            if len(netloc_parts) > 1:
                site = netloc_parts[0]
            self.manifest_table_name = site + ViewCount.MANIFEST_TABLE_NAME

        self.manifest_db_handler = DynamoDBHandler(self.manifest_table_name)

        self.logger.debug("Valid repo url: " + path)
        try:
            # First see record already exists in DB
            tx_manifest = TxManifest({'repo_name': repo_name, 'user_name': repo_owner}, db_handler=self.manifest_db_handler)
            if tx_manifest.repo_name:
                if increment:
                    tx_manifest.views += 1
                    self.logger.debug('Incrementing view count to {0}'.format(tx_manifest.views))
                    tx_manifest.update()
            else:  # table is not present
                tx_manifest.views = 0
                if increment:
                    self.logger.debug('Inserting new page into manifest table')
                    tx_manifest.views += 1
                    manifest_data = {
                        'repo_name': repo_name,
                        'user_name': repo_owner,
                        'lang_code': 'UNKNOWN',
                        'resource_id': 'UNKNOWN',
                        'resource_type': 'UNKNOWN',
                        'title': 'UNKNOWN',
                        'last_updated': None,
                        'manifest': '{}',
                        'views': tx_manifest.views
                    }
                    tx_manifest.populate(manifest_data)
                    tx_manifest.insert()
                else:
                    self.logger.debug('No entries for page in manifest table')

            response['view_count'] = str(tx_manifest.views)
        except Exception as e:
            self.logger.exception('Error accessing manifest', exc_info=e)
            response['ErrorMessage'] = ViewCount.DB_ACCESS_ERROR + path
            return response

        del response['ErrorMessage']
        return response