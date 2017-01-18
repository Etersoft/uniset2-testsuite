#!/usr/bin/env python
# -*- coding: utf-8 -*-

from TestSuiteGlobal import *

''' Вывод в формате junit '''


class TestSuiteJUnitReporter(TestSuiteReporter):
    def __init__(self):
        TestSuiteReporter.__init__(self)

        self.logfilename = ""

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
        pass

    def print_actlog(self, act):
        pass

    def make_report(self, results, checkScenarioMode=False):
        pass
        # try:
        #
        #     beg = False
        #     t_stack = []
        #     testlist = []
        #     t_name = ""
        #     for l in self.tsi.log_list:
        #         i = self.tsi.re_log.findall(l)
        #
        #         if len(i) == 0 or len(i[0]) < logid.Num:
        #             print 'UNKNOWN LOG FORMAT: %s' % str(l)
        #             continue
        #
        #         r = i[0]
        #         if r[logid.TestType] == 'BEGIN':
        #             beg = True
        #             t_name = r[logid.Txt]
        #             t_stack = []
        #         elif r[logid.TestType] == 'FINISH' and beg == True:
        #             t_info = self.tsi.re_tinfo.findall(r[logid.Txt])
        #             t_r = t_info[0]
        #             t_sec = int(t_r[1]) * 60 * 60 + int(t_r[1]) * 60 + int(t_r[3])
        #             t_time = "%d.%s" % (t_sec, t_r[4])
        #
        #             testlist.append([t_name, r[logid.Result], t_time, r[logid.Txt], t_stack, l])
        #             beg = False
        #             t_stack = []
        #         elif beg == True:
        #             t_stack.append([r, l])
        #
        #     repfile = open(repfilename, "w")
        #     repfile.writelines('<?xml version="1.0" encoding="UTF-8"?>\n')
        #     repfile.writelines('<testsuite name="%s" tests="%d">\n' % (self.filename, len(testlist)))
        #
        #     tnum = 1
        #     for r in testlist:
        #         if r[1] == t_PASSED:
        #             repfile.writelines('  <testcase name="%s" time="%s" id="%d"/>\n' % (r[0], r[2], tnum))
        #         else:
        #             repfile.writelines('  <testcase name="%s" time="%s" id="%d">\n' % (r[0], r[2], tnum))
        #             if r[1] == t_IGNORE:
        #                 repfile.writelines('    </skipped>\n')
        #             elif r[1] != t_PASSED:
        #                 repfile.writelines('    <failure>%s</failure>\n' % (r[3]))
        #                 repfile.writelines('    <system-err>\n')
        #                 for l in r[4]:
        #                     if l[0][logid.Result] == 'FAILED':
        #                         repfile.writelines('%s\n' % str(l[1]))
        #                 repfile.writelines('    </system-err>\n')
        #
        #                 repfile.writelines('    <system-out>\n')
        #                 for l in r[4]:
        #                     repfile.writelines('%s\n' % str(l[1]))
        #                 repfile.writelines('    </system-out>\n')
        #
        #             repfile.writelines('  </testcase>\n')
        #
        #         tnum += 1
        #
        #     repfile.writelines('</testsuite>\n')
        #     repfile.close()
        # except IOError:
        #     pass
