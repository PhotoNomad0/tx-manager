import os
import json
from __future__ import print_function, unicode_literals
from libraries.checkers.checker import Checker
from libraries.aws_tools.lambda_handler import LambdaHandler
from glob import glob
from libraries.general_tools.file_utils import read_file


class MarkdownChecker(Checker):

    def run(self):
        """
        Checks for issues with all Markdown project, such as bad use of headers, bullets, etc.

        Use self.log.warning("message") to log any issues.
        self.preconvert_dir is the directory of pre-converted files (.usfm)
        self.converted_dir is the directory of converted files (.html)
        :return:
        """
        lambda_handler = LambdaHandler()
        lint_function = '{0}tx_markdown_linter'.format(self.prefix)
        for f in sorted(glob(os.path.join(self.preconvert_dir, '*.md'))):
            filename = os.path.basename(f)
            response = lambda_handler.invoke(lint_function, {'options': {'strings': {filename: read_file(f)}}})
            if 'errorMessage' in response:
                self.log.error(response['errorMessage'])
            elif 'Payload' in response:
                lint = response['Payload'].read()
                for line in sorted(lint.split('\n')):
                    self.log.warning(line)
