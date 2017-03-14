#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from TestSuiteConsoleReporter import *


class TestSuiteLogFileReporter(TestSuiteConsoleReporter):
    '''
    Класс реализующий вывод лога в файл. Управляется аргументами командной строки
    начинающимися с префикса --logfile-xxxx.
    Построен на основе TestSuiteConsoleReporter, просто перенапрявляет вывод вместо экрана в файл.
    '''

    def __init__(self, arg_prefix='logfile', **kwargs):
        TestSuiteConsoleReporter.__init__(self, 'log', **kwargs)

        self.logfile_name = ""
        self.logfile_flush = False
        self.logfile_trunc = False
        self.logfile = None

        TestSuiteReporter.commandline_to_attr(self, arg_prefix, 'logfile')
        self.log_no_coloring_output = True

        if self.is_enabled():
            mode = 'a'
            if self.logfile_trunc:
                mode = 'w'

            self.logfile = open(self.logfile_name, mode)

    def __del__(self):
        if self.logfile:
            self.logfile.close()

    @staticmethod
    def print_help(prefix='logfile'):

        print 'TestSuiteLogFileReporter (--' + prefix + ')'
        print '--------------------------------------------'
        print '--' + prefix + '-name filename  - Save log to file'
        print '--' + prefix + '-trunc          - Truncate logile'
        print '--' + prefix + '-flush          - flush every write'

    def is_enabled(self):
        return (len(self.logfile_name) > 0)

    def finish_test_event(self):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = self.logfile
        sys.stderr = self.logfile
        try:
            TestSuiteConsoleReporter.finish_test_event(self)
            if self.logfile_flush:
                sys.stdout.flush()
        except:
            pass

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def print_log(self, item):

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = self.logfile
        sys.stderr = self.logfile
        try:
            TestSuiteConsoleReporter.print_log(self, item)
            if self.logfile_flush:
                sys.stdout.flush()
        except:
            pass

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def print_actlog(self, act):

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = self.logfile
        sys.stderr = self.logfile
        try:
            TestSuiteConsoleReporter.print_actlog(self, act)
            if self.logfile_flush:
                sys.stdout.flush()
        except:
            pass

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def make_report(self, tree_tests, check_scenario_mode=False):

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = self.logfile
        sys.stderr = self.logfile
        try:
            TestSuiteConsoleReporter.make_report(self, tree_tests, check_scenario_mode)
            sys.stdout.flush()
        except:
            pass

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
