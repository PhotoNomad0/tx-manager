from __future__ import absolute_import, unicode_literals, print_function
import json
import os
import shutil
import tempfile
import unittest
import boto3
import mock
from datetime import datetime
from libraries.client.client_webhook import ClientWebhook
from libraries.general_tools.file_utils import read_file
from libraries.models.manifest import TxManifest
from moto import mock_s3
from libraries.app.app import App
from libraries.general_tools.file_utils import json_serial
from tests.client_tests import mock_utils


@mock_s3
class ClientWebhookTest(unittest.TestCase):
    parent_resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    base_temp_dir = os.path.join(tempfile.gettempdir(), 'test-tx-manager')
    mock_gogs = None

    @classmethod
    def setUpClass(cls):
        ClientWebhookTest.patches = (
            mock.patch('libraries.gogs_tools.gogs_handler.GogsHandler.get_user', mock_utils.get_user),
        )
        for patch in ClientWebhookTest.patches:
            patch.start()

    @classmethod
    def tearDownClass(cls):
        for patch in ClientWebhookTest.patches:
            patch.stop()

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        App.cdn_s3_handler().create_bucket()
        App.pre_convert_s3_handler().create_bucket()
        App.cdn_s3_handler().upload_file = self.mock_cdn_upload_file
        App.cdn_s3_handler().get_json = self.mock_cdn_get_json
        App.pre_convert_s3_handler().upload_file = self.mock_s3_upload_file

        try:
            os.makedirs(ClientWebhookTest.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='webhookTest_')
        self.job_converter_count = 0
        self.job_linter_count = 0
        self.uploaded_files = []

        self.job_data = {
            'job_id': '0',
            'status': 'started',
            'success': 'success',
            'resource_type': 'obs',
            'input_format': 'md',
            'output_format': 'html',
            'convert_module': 'module1',
            'created_at': datetime.utcnow(),
            'errors': []
        }

    def tearDown(self):
        """Runs after each test."""
        App.db_close()
        shutil.rmtree(ClientWebhookTest.base_temp_dir, ignore_errors=True)

    @mock.patch('libraries.client.client_webhook.download_file')
    def test_download_repo(self, mock_download_file):
        mock_download_file.side_effect = self.mock_download_file
        cwh = ClientWebhook()
        try:
            os.makedirs(cwh.base_temp_dir)
        except:
            pass
        cwh.download_repo('bible_bundle_master', ClientWebhookTest.base_temp_dir)

    @mock.patch('libraries.client.client_webhook.download_file')
    def test_process_webhook(self, mock_download_file):
        # given
        client_web_hook = self.setup_client_webhook_mock('kpb_mat_text_udb_repo', self.parent_resources_dir,
                                                         mock_download_file)
        expected_job_count = 1
        expected_error_count = 0

        # when
        results = client_web_hook.process_webhook()

        # then
        self.validateResults(results, expected_job_count, expected_error_count)

        # Check repo was added to manifest table
        repo_name = client_web_hook.commit_data['repository']['name']
        user_name = client_web_hook.commit_data['repository']['owner']['username']
        tx_manifest = TxManifest.get(repo_name=repo_name, user_name=user_name)
        self.assertEqual(tx_manifest.repo_name, client_web_hook.commit_data['repository']['name'])
        self.assertEqual(tx_manifest.resource_id, 'udb')
        self.assertEqual(tx_manifest.lang_code, 'kpb')

    @mock.patch('libraries.client.client_webhook.download_file')
    @mock.patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhookError(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        mock_send_payload_to_run_linter.return_value = {'success': True, 'warnings': []}
        client_web_hook = self.setup_client_webhook_mock('kpb_mat_text_udb_repo', self.parent_resources_dir,
                                                         mock_download_file)
        self.job_data['errors'] = ['error 1', 'error 2']
        expected_job_count = 1
        expected_error_count = 2

        # when
        try:
            client_web_hook.process_webhook()
        except:
            pass

        # then
        self.validateResults(self.get_build_log_json(), expected_job_count, expected_error_count)

    @mock.patch('libraries.client.client_webhook.download_file')
    @mock.patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_process_webhook_update_manifest_table(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        manifest_data = {
            'resource_id': ' ',
            'title': ' ',
            'manifest':  ' ',
            'lang_code': ' ',
            'user_name': 'tx-manager-test-data',
            'resource_type': ' ',
            'repo_name': 'en-ulb'}
        tx_manifest = TxManifest(**manifest_data)
        tx_manifest.insert()  # preload table with empty data
        mock_send_payload_to_run_linter.return_value = {'success': True, 'warnings': []}
        client_web_hook = self.setup_client_webhook_mock('kpb_mat_text_udb_repo', self.parent_resources_dir,
                                                         mock_download_file)
        expected_job_count = 1
        expected_error_count = 0

        # when
        results = client_web_hook.process_webhook()

        # then
        self.validateResults(results, expected_job_count, expected_error_count)

        # Check repo was updated in manifest table
        repo_name = client_web_hook.commit_data['repository']['name']
        user_name = client_web_hook.commit_data['repository']['owner']['username']
        tx_manifest = TxManifest.get(repo_name=repo_name, user_name=user_name)
        self.assertEqual(tx_manifest.repo_name, client_web_hook.commit_data['repository']['name'])
        self.assertEqual(tx_manifest.resource_id, 'udb')
        self.assertEqual(tx_manifest.lang_code, 'kpb')
        self.assertEqual(tx_manifest.title, 'Unlocked Dynamic Bible')
        self.assertEqual(tx_manifest.resource_type, 'book')
        self.assertGreater(len(tx_manifest.manifest), 100)

    @mock.patch('libraries.client.client_webhook.download_file')
    @mock.patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhookMultipleBooks(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        self.setup_linter()
        self.linter_success = True
        self.linter_warnings = []
        mock_send_payload_to_run_linter.side_effect = self.mock_send_payload_to_run_linter
        client_web_hook = self.setup_client_webhook_mock(os.path.join('raw_sources', 'en-ulb'),
                                                         self.resources_dir, mock_download_file)
        expected_job_count = 4
        expected_error_count = 0
        expected_warnings_count = expected_job_count * len(self.linter_warnings)

        # when
        results = client_web_hook.process_webhook()

        # then
        self.validateResults2(results, expected_job_count, expected_error_count, expected_warnings_count)

    @mock.patch('libraries.client.client_webhook.download_file')
    @mock.patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhookMultipleBooksWarnings(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        self.setup_linter()
        self.linter_success = True
        self.linter_warnings = ["warning!!"]
        mock_send_payload_to_run_linter.side_effect = self.mock_send_payload_to_run_linter
        client_web_hook = self.setup_client_webhook_mock(os.path.join('raw_sources', 'en-ulb'),
                                                         self.resources_dir, mock_download_file)
        expected_job_count = 4
        expected_error_count = 0
        expected_warnings_count = expected_job_count * len(self.linter_warnings)

        # when
        results = client_web_hook.process_webhook()

        # then
        self.validateResults2(results, expected_job_count, expected_error_count, expected_warnings_count)

    @mock.patch('libraries.client.client_webhook.download_file')
    @mock.patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhookMultipleBooksLinterFail(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        self.setup_linter()
        self.linter_success = False
        self.linter_warnings = []
        mock_send_payload_to_run_linter.side_effect = self.mock_send_payload_to_run_linter
        client_web_hook = self.setup_client_webhook_mock(os.path.join('raw_sources', 'en-ulb'),
                                                         self.resources_dir, mock_download_file)
        expected_job_count = 4
        expected_error_count = 0
        expected_warnings_count = expected_job_count

        # when
        results = client_web_hook.process_webhook()

        # then
        self.validateResults2(results, expected_job_count, expected_error_count, expected_warnings_count)

    @mock.patch('libraries.client.client_webhook.download_file')
    @mock.patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhookMultipleBooksErrors(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        client_web_hook = self.setup_client_webhook_mock(os.path.join('raw_sources', 'en-ulb'), self.resources_dir,
                                                         mock_download_file)
        self.setup_linter()
        self.linter_success = True
        self.linter_warnings = ["warning!!"]
        mock_send_payload_to_run_linter.side_effect = self.mock_send_payload_to_run_linter
        self.job_data['errors'] = ['error 1', 'error 2']
        expected_job_count = 4
        expected_error_count = 2 * expected_job_count
        expected_warnings_count = expected_job_count * len(self.linter_warnings)

        # when
        try:
            client_web_hook.process_webhook()
            captured_error = False
        except:
            captured_error = True

        print(self.get_build_log_json())

        # then
        self.assertTrue(captured_error)
        self.validateResults2(self.get_build_log_json(), expected_job_count, expected_error_count,
                              expected_warnings_count)

    #
    # helpers
    #

    def validateResults2(self, results, expected_job_count, expected_error_count, expected_warnings_count):
        self.assertEqual(len(results['warnings']), expected_warnings_count)
        self. validateResults(results, expected_job_count, expected_error_count)

    def validateResults(self, results, expected_job_count, expected_error_count):
        multiple_job = expected_job_count > 1
        self.assertEqual(self.job_converter_count, expected_job_count)
        self.assertTrue(len(results['job_id']) > 16)
        self.assertTrue(len(results['commit_id']) > 8)
        self.assertTrue(len(results['repo_owner']) > 1)
        self.assertTrue(len(results['repo_name']) > 1)
        if multiple_job:
            self.assertEqual(len(results['build_logs']), expected_job_count)
            self.assertTrue(len(results['source']) > 1)
        self.assertEqual(len(results['errors']), expected_error_count)
        self.assertEqual(multiple_job, 'multiple' in results)
        self.maxDiff = None
        self.assertDictEqual(json.loads(json.dumps(results, default=json_serial)), self.get_build_log_json())
        self.assertTrue(len(self.get_project_json()) >= 4)

    def get_build_log_json(self):
        return self.read_last_uploaded_json_file('build_log.json')

    def get_project_json(self):
        return self.read_last_uploaded_json_file('project.json')

    def read_last_uploaded_json_file(self, match):
        json_str = self.read_last_uploaded_file(match)
        if json_str:
            json_data = json.loads(json_str)
            return json_data
        return None

    def read_last_uploaded_file(self, match):
        file_path = self.get_last_uploaded_file(match)
        if file_path:
            return read_file(file_path)
        return None

    def get_last_uploaded_file(self, match):
        for upload in reversed(self.uploaded_files):
            if match in upload['key']:
                return upload['file']
        return None

    def setup_client_webhook_mock(self, repo_name, base_path, mock_download_file):
        App.gogs_url = base_path
        App.gogs_user_token = mock_utils.valid_token
        mock_download_file.side_effect = self.mock_download_file
        source = os.path.join(base_path, repo_name)
        commit_data = self.get_commit_data(source)
        self.cwh = ClientWebhook(commit_data)
        self.cwh.send_payload_to_converter = self.mock_send_payload_to_converter
        self.cwh.clear_commit_directory_in_cdn = self.mock_clear_commit_directory_in_cdn
        return self.cwh

    def mock_download_file(self, source, target):
        if source != target:
            shutil.copyfile(os.path.join(ClientWebhookTest.parent_resources_dir, source), target)

    def mock_send_payload_to_converter(self, payload, converter):
        self.job_converter_count += 1
        return True

    def mock_send_payload_to_run_linter(self, payload, linter):
        self.job_linter_count += 1
        return True

    def mock_cdn_upload_file(self, project_file, s3_key):
        bucket_name = App.pre_convert_s3_handler().bucket.name
        return self.upload_file(bucket_name, project_file, s3_key)

    def mock_s3_upload_file(self, project_file, s3_key):
        bucket_name = App.cdn_s3_handler().bucket.name
        return self.upload_file(bucket_name, project_file, s3_key)

    def upload_file(self, bucket_name, project_file, s3_key):
        filename = tempfile.mktemp(dir=ClientWebhookTest.base_temp_dir)
        shutil.copyfile(project_file, filename)
        self.uploaded_files.append({'file': filename, 'key': bucket_name + '/' + s3_key})
        return

    def mock_cdn_get_json(self, project_json_key):
        return {}

    def mock_clear_commit_directory_in_cdn(self, s3_results_key):
        return

    def setup_linter(self):
        try:
            #setup linter messaging
            sqs = boto3.resource('sqs')
            sqs.create_queue(QueueName=App.linter_messaging_name, Attributes={'DelaySeconds': '5'})
        except:
            pass

    def get_commit_data(self, source_path):
        base_url = 'https://git.door43.org'
        commit_id = '22f3d09f7a33d2496db6993648f0cd967a9006f6'
        commit_path = '/tx-manager-test-data/en-ulb/commit/22f3d09f7a33d2496db6993648f0cd967a9006f6'
        repo = 'en-ulb'
        user = 'tx-manager-test-data'

        if not source_path:
            source_path = base_url + commit_path

        commit_data = {
            'after': commit_id,
            'commits': [
                {
                    'id': commit_id,
                    'message': 'Fri Dec 16 2016 11:09:07 GMT+0530 (India Standard Time)\n',
                    'url': source_path,
                }],
            'compare_url': '',
            'repository': {
                'name': repo,
                'owner': {
                    'id': '1234567890',
                    'username': user,
                    'full_name': user,
                    'email': 'you@example.com'
                },
            },
            'pusher': {
                'id': '123456789',
                'username': 'test',
                'full_name': '',
                'email': 'you@example.com'
            },
        }
        return commit_data
