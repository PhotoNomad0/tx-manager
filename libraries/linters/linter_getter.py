from __future__ import print_function, unicode_literals

from libraries.linters.usfm_linter import UsfmLinter
from libraries.linters.obs_linter import ObsLinter
from libraries.linters.udb_linter import UdbLinter
from libraries.linters.ulb_linter import UlbLinter
from libraries.linters.ta_linter import TaLinter
from libraries.linters.tn_linter import TnLinter
from libraries.linters.tq_linter import TqLinter
from libraries.linters.tw_linter import TwLinter
from libraries.linters.markdown_linter import MarkdownLinter
from libraries.resource_container.ResourceContainer import BIBLE_RESOURCE_TYPES


class LinterGetter:
    @staticmethod
    def get_linter_class(resource=None, file_type=None):
        if resource == 'obs':
            return ObsLinter
        elif resource == 'ta':
            return TaLinter
        elif resource == 'tn':
            return TnLinter
        elif resource == 'tq':
            return TqLinter
        elif resource == 'tw':
            return TwLinter
        elif resource == 'udb':
            return UdbLinter
        elif resource == 'ulb':
            return UlbLinter
        elif resource in BIBLE_RESOURCE_TYPES or file_type == 'usfm':
            return UsfmLinter
        elif file_type == 'md':
            return MarkdownLinter
        else:
            return MarkdownLinter
