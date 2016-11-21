#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import string
from TestSuiteGlobal import *

''' Вывод на экран (надо сделать Singleton-ом!) '''
class TestSuiteConsoleReporter(TestSuiteReporter):
    def __init__(self):
        TestSuiteReporter.__init__(self)

        self.colsep = ":"  # символ разделитель столбцов (по умолчанию)
        self.col_comment_width = 50
        self.log_numstr = 0
        self.log_show_numline = False
        self.printlog = False
        self.printactlog = False
        self.notimestamp = False
        self.show_test_type = False
        self.log_show_comments = False
        self.log_show_test_comment = False
        self.log_hide_time = False
        self.log_hide_msec = False
        self.log_show_testtype = False
        self.log_list = []
        self.no_coloring_output = False

    def print_log(self, item):
        txt = self.make_log(item)
        if self.printlog:
            print txt

    def make_log(self, item):

        t_comment = item['comment']
        t_test = item['type']
        txt = item['text']
        t_result = item['result']
        try:
            if t_comment != None and len(t_comment) > 0:
                t_comment = unicode(t_comment, "UTF-8", errors='replace')
        except UnicodeDecodeError:
            pass
        except TypeError:
            pass

        self.log_numstr += 1
        t_tm = str(time.strftime('%Y-%m-%d %H:%M:%S'))
        txt2 = self.set_tab_space(txt, item['nrecur'], item['ntab'])

        txt = str('[%s] %s%8s%s %s' % (
            self.colorize_result(t_result), self.colsep, t_test, self.colsep,
            self.colorize_text(t_result, t_test, txt2)))
        txt3 = str('[%7s] %s%8s%s %s' % (t_result, self.colsep, t_test, self.colsep, txt2))
        # llog = '%s %s%s' % (t_tm, self.colsep, txt3)

        if not self.log_show_testtype:
            txt = str('[%s] %s %s' % (
                self.colorize_result(t_result), self.colsep, self.colorize_text(t_result, t_test, txt2)))

        if self.log_show_comments or self.log_show_test_comment:
            if not t_comment or (self.log_show_test_comment and not self.log_show_comments and t_test != 'BEGIN'):
                t_comment = ""

            try:
                t_comment = unicode(t_comment, "UTF-8", errors='replace')
            except UnicodeDecodeError:
                pass
            except TypeError:
                pass
            try:
                txt = '%s %s %s' % (
                    self.colorize_text(t_result, t_test,
                                       t_comment.ljust(self.col_comment_width)[0:self.col_comment_width]),
                    self.colsep, txt)
            except UnicodeDecodeError:
                pass
            except TypeError:
                pass

        etm = self.elapsed_time_str()
        # llog = '%s %s %s' % (etm, self.colsep, llog)

        if not self.log_hide_time:
            txt = '%s %s %s' % (etm, self.colsep, txt)

        # llog = '%6s %s %s' % ("CHECK", self.colsep, llog)
        if self.show_test_type:
            txt = '%6s %s %s' % ("CHECK", self.colsep, txt)

        if not self.notimestamp:
            txt = "%s %s%s" % (t_tm, self.colsep, txt)

        if self.log_show_numline:
            txt = '%4s %s %s' % (self.log_numstr, self.colsep, txt)

        return txt

    def print_actlog(self, act):

        txt = self.make_actlog(act)
        if self.printactlog:
            print txt

    def make_actlog(self, act):
        t_comment = act['comment']
        t_act = act['type']
        txt = act['text']
        t_result = act['result']

        try:
            if t_comment != None and len(t_comment) > 0:
                t_comment = unicode(t_comment, "UTF-8", errors='replace')
        except UnicodeDecodeError:
            pass
        except TypeError:
            pass

        self.log_numstr += 1
        t_tm = str(time.strftime('%Y-%m-%d %H:%M:%S'))
        txt2 = self.set_tab_space(txt, act['nrecur'], act['ntab'])
        txt3 = str('[%7s] %s%8s%s %s' % (t_result, self.colsep, t_act, self.colsep, txt2))
        llog = '%s %s%s' % (t_tm, self.colsep, txt3)

        txt = str('[%7s] %s%8s%s %s' % (
            self.colorize_result(t_result), self.colsep, t_act, self.colsep, self.colorize_text(t_result, t_act, txt2)))

        if not self.log_show_testtype:
            txt = str('[%7s] %s %s' % (
                self.colorize_result(t_result), self.colsep, self.colorize_text(t_result, t_act, txt2)))

        if self.log_show_comments or self.log_show_test_comment:
            if not t_comment or (self.log_show_test_comment and not self.log_show_comments and t_act != 'BEGIN'):
                t_comment = ""

            try:
                t_comment = unicode(t_comment, "UTF-8", errors='replace')
            except UnicodeDecodeError:
                pass
            except TypeError:
                pass

            try:
                txt = '%s %s %s' % (
                    self.colorize_text(t_result, t_act,
                                       t_comment.ljust(self.col_comment_width)[0:self.col_comment_width]),
                    self.colsep, txt)
            except UnicodeDecodeError:
                pass
            except TypeError:
                pass

        etm = self.elapsed_time_str()
        # llog = '%s %s %s' % (etm, self.colsep, llog)
        if not self.log_hide_time:
            txt = '%s %s %s' % (etm, self.colsep, txt)

        llog = '%6s %s %s' % ('ACTION', self.colsep, llog)
        if self.show_test_type:
            txt = '%6s %s %s' % ('ACTION', self.colsep, txt)

        if not self.notimestamp:
            txt = '%s %s%s' % (t_tm, self.colsep, txt)

        if self.log_show_numline:
            txt = '%4s %s %s' % (self.log_numstr, self.colsep, txt)

        return txt

    def makeReport(self, results):

        filename = ''
        if len(results) > 0:
            filename = results[0]

        head = "\nRESULT REPORT: '%s'" % filename
        head2 = ""
        foot2 = ""
        for i in range(0, len(head)):
            head2 += '*'
            foot2 += "-"

        print "%s\n%s" % (head, head2)
        i = 1
        ttime = 0
        for res in results:
            td = datetime.timedelta(0, res['time'])
            print '%s. [%s] - %40s |%s|' % (
                string.rjust(str(i), 3), self.colorize_result(res['result']), string.ljust(res['name'], 45),
                td)
            i = i + 1
            ttime = ttime + res['time']

        # td = datetime.timedelta(0, ttime)
        # ts = str(td).split('.')[0]
        print foot2
        print 'Total time: %s\n' % self.elapsed_time_str()

    def colorize(self, t_result, txt):

        if self.no_coloring_output:
            return txt

        if t_result == t_PASSED:
            return "\033[1;32m%s\033[1;m" % txt
        if t_result == t_WARNING or t_result == t_UNKNOWN:
            return "\033[1;33m%s\033[1;m" % txt
        if t_result == t_FAILED:
            return "\033[1;31m%s\033[1;m" % txt
        if t_result == t_IGNORE:
            return "\033[1;34m%s\033[1;m" % txt

        return txt

    def colorize_test_begin(self, txt):
        if self.no_coloring_output:
            return txt

        return "\033[1;37m%s\033[1;m" % txt

    def colorize_test_finish(self, txt):

        # пока не будем расскрашивать "finish"
        return txt
        # return self.colorize_test_name(txt)

    def colorize_test_outlink(self, txt):
        if self.no_coloring_output:
            return txt

        return "\033[1;36m%s\033[1;m" % txt

    def colorize_text(self, t_result, t_test, txt):

        # раскрашиваем только t_FAILED
        if t_result == t_FAILED:
            return self.colorize(t_result, txt)

        if t_test == 'BEGIN':
            return self.colorize_test_begin(txt)

        if t_test == 'FINISH':
            return self.colorize_test_finish(txt)

        if t_test == 'OUTLINK':
            return self.colorize_test_outlink(txt)

        return txt

    def colorize_result(self, t_result):
        return self.colorize(t_result, "%7s" % t_result)

    def set_notime(self, state):
        self.log_hide_time = state

    def set_notimestamp(self, state):
        self.notimestamp = state

    def elapsed_time(self, t=None):
        if t is None:
            t = time.time() - self.start_time

        h = int(t / 3600.0)
        t -= 3600 * h
        m = int(t / 60)
        s = int(t - m * 60)
        t -= s
        return [h, m, s, t]

    def elapsed_time_str(self, t=None):
        h, m, s, t = self.elapsed_time(t)
        if self.log_hide_msec:
            return '%02d:%02d:%02d' % (h, m, s)

        return '%02d:%02d:%02d [%7.3f]' % (h, m, s, t)

    def format_comment(self, txt):
        t_comment = txt
        try:
            t_comment = unicode(txt, "UTF-8", errors='replace')
        except UnicodeDecodeError:
            pass
        except TypeError:
            pass

        try:
            t_comment = '%s' % t_comment.ljust(self.col_comment_width)[0:self.col_comment_width]
        except UnicodeDecodeError:
            pass
        except TypeError:
            pass

        return t_comment

    @staticmethod
    def set_tab_space(txt, nrecur, ntab):
        # сдвиг "уровня" в зависимости от рекурсии
        s_tab = ""
        if nrecur > 0:
            for i in range(0, nrecur):
                s_tab = '%s.   ' % s_tab
        txt = '%s%s' % (s_tab, txt)

        if ntab:
            txt = '.   %s' % txt

        return txt

    def set_show_comments(self, show_comments):
        self.log_show_comments = show_comments

    def set_show_numline(self, show_numline):
        self.log_show_numline = show_numline

    def set_hide_time(self, hide_time):
        self.log_hide_time = hide_time

    def set_show_test_type(self, show_test_type):
        self.log_show_testtype = show_test_type

    def set_col_comment_width(self, col_comment_width):
        self.col_comment_width = col_comment_width

    def set_show_test_comment(self, show_test_comment):
        self.log_show_test_comment = show_test_comment
