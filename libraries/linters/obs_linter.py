from __future__ import print_function, unicode_literals
import os
from bs4 import BeautifulSoup
from libraries.linters.markdown_linter import MarkdownLinter
from libraries.linters.obs_data import obs_data
from libraries.general_tools.file_utils import read_file


class ObsLinter(MarkdownLinter):

    def lint(self):
        """
        Checks for issues with OBS

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return:
        """
        super(self, ObsLinter).lint()

