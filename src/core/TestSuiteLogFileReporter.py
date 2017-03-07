#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from TestSuiteConsoleReporter import *

''' Запись отчёта в лог файл (надо сделать Singleton-ом!) '''


class TestSuiteLogFileReporter(TestSuiteConsoleReporter):
    def __init__(self, **kwargs):
        TestSuiteConsoleReporter.__init__(self, **kwargs)

        self.log_filename = ""
        self.log_flush = False

        for k,v in kwargs.items():
            if hasattr(self, k):
                setattr(self,k,v)

    def set_logfile(self, fname, trunc=False):
        self.log_filename = fname
        if self.log_filename == "" or self.log_filename == None:
            return
        if trunc:
            logfile = open(self.log_filename, 'w')
            logfile.close()

    def get_logfile(self):
        return self.log_filename

    def print_log(self, item):

        txt = self.make_log(item)
        self.write_logfile(txt)
        if self.log_flush:
            sys.stdout.flush()

    def print_actlog(self, act):

        txt = self.make_actlog(act)
        self.write_logfile(txt)
        if self.log_flush:
            sys.stdout.flush()

    def write_logfile(self, txt):
        if self.log_filename == "" or self.log_filename == None:
            return
        try:
            logfile = open(self.log_filename, 'a')
            logfile.writelines(txt)
            logfile.writelines('\n')
            logfile.close()
        except IOError:
            pass

    def make_report(self, results, check_scenario_mode=False):
        pass
