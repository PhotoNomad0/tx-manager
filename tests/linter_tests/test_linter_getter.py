from __future__ import absolute_import, unicode_literals, print_function
import unittest
from libraries.linters.linter_getter import LinterGetter


class TestLinterGetter(unittest.TestCase):

    def tes_get_linter_class(self):
        self.assertEqual(LinterGetter.get_linter_class('bible').__name__, 'UsfmLinter')
        self.assertEqual(LinterGetter.get_linter_class('obs').__name__, 'ObsLinter')
        self.assertEqual(LinterGetter.get_linter_class('ta').__name__, 'TaLinter')
        self.assertEqual(LinterGetter.get_linter_class('tn').__name__, 'TnLinter')
        self.assertEqual(LinterGetter.get_linter_class('tq').__name__, 'TqLinter')
        self.assertEqual(LinterGetter.get_linter_class('tw').__name__, 'TwLinter')
        self.assertEqual(LinterGetter.get_linter_class('udb').__name__, 'UdbLinter')
        self.assertEqual(LinterGetter.get_linter_class('ulb').__name__, 'UlbLinter')
        self.assertEqual(LinterGetter.get_linter_class(None, 'usfm').__name__, 'UsfmLinter')
        self.assertEqual(LinterGetter.get_linter_class(None, 'md').__name__, 'MarkdownLinter')
        self.assertEqual(LinterGetter.get_linter_class('something').__name__, 'MarkdownLinter')
        self.assertEqual(LinterGetter.get_linter_class().__name__, 'MarkdownLinter')
