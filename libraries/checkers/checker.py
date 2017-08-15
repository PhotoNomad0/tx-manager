from __future__ import print_function, unicode_literals
from abc import ABCMeta, abstractmethod
from libraries.converters.convert_logger import ConvertLogger
from libraries.manager.manager import TxManager


class Checker(object):
    __metaclass__ = ABCMeta

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
