from __future__ import print_function, unicode_literals
import os
from abc import ABCMeta, abstractmethod
from libraries.converters.convert_logger import ConvertLogger


class Checker(object):
    __metaclass__ = ABCMeta
    EXCLUDED_FILES = ["license.md", "package.json", "project.json", 'readme.md']

    def __init__(self, preconvert_dir, converted_dir, log=None, prefix=''):
        """
        :param string preconvert_dir:
        :param string converted_dir:
        :param ConvertLogger log:
        :param string prefix:
        """
        self.preconvert_dir = preconvert_dir
        self.converted_dir = converted_dir
        self.log = log
        self.prefix = prefix
        if not self.log:
            self.log = ConvertLogger()

    @abstractmethod
    def run(self):
        pass
