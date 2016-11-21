#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import string
from TestSuiteGlobal import *
from TestSuiteConsoleReporter import *

''' Запись отчёта в лог файл (надо сделать Singleton-ом!) '''
class TestSuiteLogFileReporter(TestSuiteConsoleReporter):

    def __init__(self):

        self.logfilename = ""
        self.log_flush = False

    def set_logfile(self, fname, trunc=False):
        self.logfilename = fname
        if self.logfilename == "" or self.logfilename == None:
            return
        if trunc:
            logfile = open(self.logfilename, 'w')
            logfile.close()

    def get_logfile(self):
        return self.logfilename

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
        if self.logfilename == "" or self.logfilename == None:
            return
        try:
            logfile = open(self.logfilename, 'a')
            logfile.writelines(txt)
            logfile.writelines('\n')
            logfile.close()
        except IOError:
            pass

    def makeReport(self, results):
        pass