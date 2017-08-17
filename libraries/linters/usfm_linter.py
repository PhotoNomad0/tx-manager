from __future__ import print_function, unicode_literals
from libraries.linters.linter import Linter


class UsfmLinter(Linter):

    def lint(self):
        """
        Checks for issues with all Bibles, such as missing books or chapters

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.usfm)
        :return:
        """
        pass
