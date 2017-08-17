from __future__ import print_function, unicode_literals

import os
import tempfile
from libraries.general_tools.url_utils import download_file
from libraries.general_tools.file_utils import unzip, remove_tree, remove
import logging
from lint_logger import LintLogger
from abc import ABCMeta, abstractmethod


class Linter(object):
    __metaclass__ = ABCMeta
    EXCLUDED_FILES = ["license.md", "package.json", "project.json", 'readme.md']

    def __init__(self, source, resource=None, file_type=None, prefix=''):
        """
        :param string source:
        :param string resource:
        :param string file_type:
        :param string prefix:
        """
        self.source = source
        self.resource = resource
        self.file_type = file_type
        self.prefix = prefix

        self.logger = logging.getLogger()
        self.log = LintLogger()

        self.download_dir = tempfile.mkdtemp(prefix='download_')
        self.source_dir = tempfile.mkdtemp(prefix='source_')
        self.source_zip_file = None  # If set, won't download the repo archive. Used for testing

    def close(self):
        """delete temp files"""
        remove_tree(self.download_dir)
        remove_tree(self.source_dir)

    @abstractmethod
    def lint(self):
        """
        Dummy function for linters.

        Returns true if it was able to lint the files
        :return bool:
        """
        raise NotImplementedError()

    def run(self):
        """
        Run common handling for all linters,and then calls the lint() function
        """
        success = True
        try:
            if not self.source_zip_file or not os.path.exists(self.source_zip_file):
                # No input zip file yet, so we need to download the archive
                self.download_archive()
            # unzip the input archive
            self.logger.debug("Unzipping {0} to {1}".format(self.source_zip_file, self.source_dir))
            unzip(self.source_zip_file, self.source_dir)
            remove(self.source_zip_file)
            # convert method called
            self.logger.debug("Linting files...")
            self.logger.debug(",,,finished.")
        except Exception as e:
            self.logger.error('Linting process ended abnormally: {0}'.format(e.message))
            success = False

        result = {
            'success': success,
            'warnings': self.log.warnings,
        }
        self.logger.debug(result)
        return result

    def download_archive(self):
        archive_url = self.source
        filename = self.source.rpartition('/')[2]
        self.source_zip_file = os.path.join(self.download_dir, filename)
        if not os.path.isfile(self.source_zip_file):
            try:
                download_file(archive_url, self.source_zip_file)
            finally:
                if not os.path.isfile(self.source_zip_file):
                    raise Exception("Failed to download {0}".format(archive_url))
