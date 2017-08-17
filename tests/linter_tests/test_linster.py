from __future__ import absolute_import, unicode_literals, print_function
import unittest
from libraries.linters.linter import Linter


class TestLinter(unittest.TestCase):

    def test_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Linter, None)
