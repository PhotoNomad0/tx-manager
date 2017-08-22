from __future__ import print_function, unicode_literals

import os
import json
from libraries.linters.linter import Linter
from libraries.aws_tools.lambda_handler import LambdaHandler
from libraries.general_tools.file_utils import read_file, get_files


class MarkdownLinter(Linter):

    def lint(self):
        """
        Checks for issues with all Markdown project, such as bad use of headers, bullets, etc.

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.usfm)
        :return:
        """
        lambda_handler = LambdaHandler()
        lint_function = '{0}tx_markdown_linter'.format(self.prefix)
        files = sorted(get_files(directory=self.source_dir, relative_paths=True, exclude=self.EXCLUDED_FILES,
                                 extensions=['.md']))
        strings = {}
        for f in files:
            path = os.path.join(self.source_dir, f)
            text = read_file(path)
            strings[f] = text
        response = lambda_handler.invoke(lint_function, {
            'options': {
                'strings': strings,
                'config': {
                    'default': True,
                    'no-hard-tabs': False,
                    'whitespace': False,
                    'line-length': False,
                    'no-inline-html': False,
                    'no-duplicate-header': False,
                    'single-h1': False,
                    'no-trailing-punctuation': False
                }
            }
        })
        if 'errorMessage' in response:
            self.log.error(response['errorMessage'])
        elif 'Payload' in response:
            lint_data = json.loads(response['Payload'].read())
            for f in lint_data.keys():
                data = lint_data[f]
                line = '{0}:{1}:{2}: {3} [{4}]'. \
                    format(f, data['lineNumber'], data['ruleAlias'], data['ruleDescription'],
                           data['ruleName'])
                self.log.warning(line)
