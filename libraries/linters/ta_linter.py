from __future__ import print_function, unicode_literals
from libraries.linters.markdown_linter import MarkdownLinter


class TaLinter(MarkdownLinter):

    def lint(self):
        """
        Checks for issues with translationAcademy

        Use self.log.warning("message") to log any issues.
        self.preconvert_dir is the directory of pre-converted files (.md)
        self.converted_dir is the directory of converted files (.html)
        :return:
        """
        super(TaLinter, self).lint()  # Runs checks on Markdown, using the markdown linter
