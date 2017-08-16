from __future__ import print_function, unicode_literals

import os
import json
from libraries.checkers.checker import Checker
from libraries.aws_tools.lambda_handler import LambdaHandler
from libraries.general_tools.file_utils import read_file, get_files


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
        self.log.info("######### " + lint_function)
        files = sorted(get_files(directory=self.preconvert_dir, extensions=['.md']))
        self.log.info('files: {0}'.format(files))
        for f in files:
            self.log.info("######### "+f)
            filename = os.path.basename(f)
            response = lambda_handler.invoke(lint_function, {'options': {'strings': {filename: read_file(f)}}})
            self.log.info("######### {}".format(response))
            if 'errorMessage' in response:
                self.log.error(response['errorMessage'])
                self.log.info("######### {}".format(response['errorMessage']))
            elif 'Payload' in response:
                lint_data = json.loads(response['Payload'].read())
                self.log.info("######### {}".format(lint_data))
                for lint in lint_data[filename]:
                    line = '{0}:{1}:{2}: {3} (Text: {4})[{5}]'. \
                        format(filename, lint['lineNumber'], lint['ruleAlias'], lint['ruleDescription'],
                               lint['errorContext'], lint['ruleName'])
                    self.log.info("######### {}".format(line))
                    self.log.warning(line)
