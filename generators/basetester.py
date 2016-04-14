import os
import sys
from abc import ABCMeta, abstractmethod

# Appending current working directory to sys.path
# So that user running randomtester from the directory where sut.py is located
current_working_dir = os.getcwd()
sys.path.append(current_working_dir)

import sut as SUT
import random
import time
import traceback
import argparse
from collections import namedtuple

class BaseTester(object):
    __metaclass__ = ABCMeta

    @staticmethod
    def parse_args(sysargs):
        """
        Parse the command-line arguments
        """
        # create parser
        parser = argparse.ArgumentParser()

        # add arguments
        parser.add_argument('-d', '--depth', type=int, default=100,
                            help='Maximum search depth (100 default).')
        parser.add_argument('-t', '--timeout', type=int, default=3600,
                            help='Timeout in seconds (3600 default).')
        parser.add_argument('-s', '--seed', type=int, default=None,
                            help='Random seed (default = None).')
        parser.add_argument('-m', '--maxtests', type=int, default=-1,
                            help='Maximum #tests to run (-1 = infinite default).')
        parser.add_argument('-u', '--uncaught', action='store_true',
                            help='Allow uncaught exceptions in actions.')
        parser.add_argument('-i', '--ignoreprops', action='store_true',
                            help='Ignore properties.')
        parser.add_argument('-f', '--full', action='store_true',
                            help="Don't reduce -- report full failing test.")
        parser.add_argument('-N', '--normalize', action='store_true',
                            help="Normalize/simplify after reduction.")
        parser.add_argument('-E', '--essentials', action='store_true',
                            help="Determine essential elements in failing test.")
        parser.add_argument('-G', '--generalize', action='store_true',
                            help="Generalize tests.")
        parser.add_argument('-D', '--gendepth', type=int, default=None,
                            help="Generalization depth for cloud overlap comparisons (default = None).")
        parser.add_argument('-e', '--speed', type=str, default="FAST",
                            help='Normalization/simplification speed (default = FAST).')
        parser.add_argument('-k', '--keep', action='store_true',
                            help="Keep last action the same when reducing.")
        parser.add_argument('-o', '--output', type=str, default=None,
                            help="Filename to save failing test(s).")
        parser.add_argument('-R', '--replayable', action='store_true',
                            help="Keep replayable file of current test, in case of crash.")
        parser.add_argument('-T', '--total', action='store_true',
                            help="Keep a file with ALL TESTING ACTIONS in case of crash.")
        parser.add_argument('-M', '--multiple', action='store_true',
                            help="Allow multiple failures.")
        parser.add_argument('-l', '--logging', type=int, default=None,
                            help="Set logging level")
        parser.add_argument('-F', '--failedLogging', type=int, default=None,
                            help="Set failed test case logging level")
        parser.add_argument('-r', '--running', action='store_true',
                            help="Produce running branch coverage report.")
        parser.add_argument('-S', '--stutter', type=float, default=None,
                            help="Repeat last action if still enabled with P = <stutter>.")
        parser.add_argument('-g', '--greedyStutter', action='store_true',
                            help="Repeat last action if it is enabled and improved coverage.")
        parser.add_argument('-n', '--nocover', action='store_true',
                            help="Don't produce a coverage report at the end.")
        parser.add_argument('-I', '--internal', action='store_true',
                            help="Produce internal coverage report at the end, as sanity check on coverage.py results.")
        parser.add_argument('-c', '--coverfile', type=str, default="coverage.out",
                            help="File to write coverage report to ('coverage.out' default).")
        parser.add_argument('-q', '--quickTests', action='store_true',
                            help="Produce quick tests for coverage.")
        parser.add_argument('-a', '--noreassign', action='store_true',
                            help="Add noReassign rule to normalization steps.")
        parser.add_argument('-v', '--verbose', action='store_true',
                            help="Run in verbose mode.")
        parser.add_argument('-H', '--html', type=str, default=None,
                            help="Write HTML report (directory to write to, None default).")

        # parse arguments
        # parsed_args = parser.parse_args(sys.argv[1:])
        parsed_args = parser.parse_args(sysargs)

        return parsed_args

    @staticmethod
    def make_config(pargs):
        """
        Process the raw arguments, returning a namedtuple object holding the
        entire configuration, if everything parses correctly.
        """
        pdict = pargs.__dict__
        # create a namedtuple object for fast attribute lookup
        key_list = pdict.keys()
        arg_list = [pdict[k] for k in key_list]
        Config = namedtuple('Config', key_list)
        nt_config = Config(*arg_list)
        return nt_config

    @abstractmethod
    def run(self, sut):
        pass
