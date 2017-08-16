from __future__ import print_function, unicode_literals
from libraries.checkers.markdown_checker import MarkdownChecker


class TwChecker(MarkdownChecker):

    def run(self):
        """
        Checks for issues with translationWords

        Use self.log.warning("message") to log any issues.
        self.preconvert_dir is the directory of pre-converted files (.md)
        self.converted_dir is the directory of converted files (.html)
        :return:
        """
        super(TwChecker, self).run()  # Runs checks on Markdown, using the markdown linter
        pass
