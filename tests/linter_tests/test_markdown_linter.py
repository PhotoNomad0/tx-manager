from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
from libraries.linters.markdown_linter import MarkdownLinter


class TestMarkdownLinter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='temp_markdown_linter_')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_lint(self):
        linter = MarkdownLinter('some_url')
        linter.source_zip_file = os.path.join(self.resources_dir, 'markdown_linter', 'en_ta.zip')
        results = linter.run()
        print(results)

