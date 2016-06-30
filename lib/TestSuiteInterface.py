#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess

# \todo может потом перейти на использование colorama
#import colorama as clr

from TestSuiteGlobal import *


class logid():
    Type = 0
    Time = 1
    msec = 2
    DateTime = 3
    Result = 4
    TestType = 5
    Txt = 6
    Num = 7


class TestSuiteInterface():
    def __init__(self):

        self.ignorefailed = False
        self.notimestamp = False
        self.log_callback = None
        self.actlog_callback = None
        self.show_test_type = False
        self.log_show_comments = False
        self.log_show_test_comment = False
        self.col_comment_width = 50
        self.log_flush = False
        self.logfilename = ""
        self.colsep = ":"  # символ разделитель столбцов (по умолчанию)
        self.ui_list = dict()
        self.conf_list = dict()
        self.default_ui = None
        self.params = Params_inst()
        self.log_numstr = 0
        self.log_show_numline = False
        self.printlog = False
        self.printactlog = False
        self.ignore_nodes = False
        self.rcheck = re.compile(r"([\w@\ :]+)([!><]*[=]*)([-\d\ ]+)")
        self.rcompare = re.compile(r"([\w@\ :]+)([!><]*[=]*)([\w@\ :]+)")
        self.beg_time = time.time()
        self.log_hide_time = False
        self.log_hide_msec = False
        self.log_show_testtype = False
        self.log_list = []
        self.nrecur = 0
        self.ntab = False
        self.no_coloring_output = False

        # "CHECK : 00:00:05 [  0.016] : 2015-03-14 02:46:06 :[ PASSED] :  FINISH: 'Global replace' /0:00:00.000837/"
        self.re_log = re.compile(
            r"([\w]+)[^:]*:[ ]*(\d{2}:\d{2}:\d{2}) \[[ ]*([\d.]+)\] : (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) :\[[ ]*([\w*]*)\][ ]*:[ ]*([^:]+):[  ]*(.*)$")

        # "'simple test' /0:00:00.001361/"
        self.re_tinfo = re.compile(r"[^/]*(/(\d+):(\d{1,2}):(\d{1,2})([.](\d*))*/)*$")

        # clr.init(autoreset=True)

    @staticmethod
    def get_aliasname(cname):
        v = cname.strip().split('@')
        if len(v) > 1:
            return [v[0], v[1]]

        # если @ не указана, то испольузем имя без точки как alias
        s = v[0].split('.')
        return [s[0], v[0]]

    def init_testsuite(self, conflist, logprn=False, logact_prn=False):

        self.printlog = logprn
        self.printactlog = logact_prn

        for i in range(0, len(sys.argv)):
            if i >= Params.max:
                break

            # confist передан отдельно
            if sys.argv[i] == '--confile' or (i != 0 and sys.argv[i - 1] == '--confile'):
                continue

            self.params.add(sys.argv[i])

        try:
            if len(conflist) == 0 or not conflist:
                return

            if conflist.__class__.__name__ != 'list':
                s = self.get_aliasname(conflist)
                if s[1] == "":
                    return

                self.default_ui = self.add_uniset_config(s[1], s[0])
            else:
                # умолчательный config - первый в списке
                s = self.get_aliasname(conflist[0])
                self.default_ui = self.add_uniset_config(s[1], s[0])
                for c in conflist:
                    s = self.get_aliasname(c)
                    if s[1] == "":
                        continue
                    self.add_uniset_config(s[1], s[0])

        except UException, e:
            self.log(t_FAILED, '(init_testsuite): ' + str(e.getError()), "", True)
            raise e

    def get_config_list(self):
        clist = []
        for c, xfile in self.conf_list.items():
            clist.append(xfile)

        # удаляем дубли..
        return [x for x in set(clist)]

    def add_uniset_config(self, xmlfile, alias, already_ignore=True):

        if to_str(xmlfile) == "":
            return

        if alias in self.ui_list:
            if not already_ignore:
                self.log(t_FAILED,
                         '(add_uniset_config): %s already added..(Ignore add \'%s@%s\')' % (alias, alias, xmlfile), "",
                         True)
                return None
            return self.ui_list[alias]

        ui = UInterface()
        ui.create_uniset_interface(xmlfile, self.params)
        ui.set_ignore_nodes(self.ignore_nodes)
        self.ui_list[alias] = ui
        self.conf_list[alias] = xmlfile
        return ui

    def add_modbus_config(self, mbslave, alias, already_ignore=True):
        if alias in self.ui_list:
            if not already_ignore:
                self.log(t_FAILED,
                         '(add_modbus_config): %s already added..(Ignore add \'%s@%s\')' % (alias, alias, mbslave), "",
                         True)
                return None
            return self.ui_list[alias]

        ip, port = get_mbslave_param(mbslave)
        if ip is None:
            self.log(t_FAILED, '(add_modbus_config): Failed get ip:port!  mbslave=\'%s\'' % (mbslave), "", True)
            return None

        ui = UInterface()
        ui.create_modbus_interface()
        ui.i.prepare(ip, port)
        self.ui_list[alias] = ui
        return ui

    def remove_config(self, alias):
        if alias in self.ui_list:
            self.ui_list.pop(alias)

    def set_default_config(self, xmlfile, already_ignore=True):
        if xmlfile in self.ui_list:
            if not already_ignore:
                self.log(t_FAILED, '(set_default_config): %s already added..(Ignore add..)' % (xmlfile), "", True)
                return False

            ui = UInterface()
            ui.create_uniset_interface(xmlfile, self.params)
            self.default_ui = ui
            self.conf_list['default'] = xmlfile

    def get_default_ui(self):
        return self.default_ui

    def set_default_ui(self, ui):
        self.default_ui = ui

    def getArgParam(self, param, defval=""):
        for i in range(0, len(sys.argv)):
            if sys.argv[i] == param:
                if i + 1 < len(sys.argv):
                    return sys.argv[i + 1]
                else:
                    break

        return defval

    @staticmethod
    def getArgInt(param, defval=0):
        for i in range(0, len(sys.argv)):
            if sys.argv[i] == param:
                if i + 1 < len(sys.argv):
                    return to_int(sys.argv[i + 1])
                else:
                    break

        return defval

    @staticmethod
    def checkArgParam(param, defval=""):
        for i in range(0, len(sys.argv)):
            if sys.argv[i] == param:
                return True

        return defval

    def set_printlog(self, prn):
        self.printlog = prn

    def set_print_actlog(self, prn):
        self.print_actlog = prn

    def set_log_callback(self, cb_func):
        self.log_callback = cb_func

    def set_actlog_callback(self, cb_func):
        self.actlog_callback = cb_func

    def set_colseparator(self, colsep):
        self.colsep = colsep

    def set_logfile(self, fname, trunc=False):
        self.logfilename = fname
        if self.logfilename == "" or self.logfilename == None:
            return
        if trunc:
            logfile = open(self.logfilename, 'w')
            logfile.close()

    def get_logfile(self):
        return self.logfilename

    def set_ignore_nodes(self, state):
        self.ignore_nodes = state
        for key, ui in self.ui_list.items():
            ui.set_ignore_nodes(state)

    def set_notimestamp(self, state):
        self.notimestamp = state

    def set_ignorefailed(self, state):
        self.ignorefailed = state

    def get_ignorefailed(self):
        return self.ignorefailed

    def start_time(self):
        self.beg_time = time.time()

    def set_notime(self, state):
        self.log_hide_time = state

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

    def elapsed_time(self, t=None):
        if t is None:
            t = time.time() - self.beg_time

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

    def set_tab_space(self, txt):
        # сдвиг "уровня" в зависимости от рекурсии
        s_tab = ""
        if self.nrecur > 0:
            for i in range(0, self.nrecur):
                s_tab = '%s.   ' % s_tab
        txt = '%s%s' % (s_tab, txt)

        if self.ntab:
            txt = '.   %s' % (txt)

        return txt

    def colorize(self, t_result, txt):

        if self.no_coloring_output:
            return txt

        if t_result == t_PASSED:
            return "\033[1;32m%s\033[1;m"%txt
        if t_result == t_WARNING or t_result == t_UNKNOWN:
            return "\033[1;33m%s\033[1;m"%txt
        if t_result == t_FAILED:
            return "\033[1;31m%s\033[1;m"%txt
        if t_result == t_IGNORE:
            return "\033[1;34m%s\033[1;m"%txt

        return txt

    def colorize_test_begin(self, txt):
        if self.no_coloring_output:
            return txt

        return "\033[1;37m%s\033[1;m"%txt

    def colorize_test_finish(self, txt):

        # пока не будем расскрашивать "finish"
        return txt
        # return self.colorize_test_name(txt)

    def colorize_test_outlink(self, txt):
        if self.no_coloring_output:
            return txt

        return "\033[1;36m%s\033[1;m"%txt

    def colorize_text(self, t_result, t_test, txt):

        # раскрашиваем только t_FAILED
        if t_result == t_FAILED:
            return self.colorize(t_result,txt)

        if t_test == 'BEGIN':
            return self.colorize_test_begin(txt)

        if t_test == 'FINISH':
            return self.colorize_test_finish(txt)

        if t_test == 'OUTLINK':
            return self.colorize_test_outlink(txt)
        return txt

    def colorize_result(self, t_result):
        return self.colorize(t_result,"%7s"%t_result)

    def format_comment(self, txt):
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

    def print_log(self, t_result, t_test, txt, t_comment):

        self.log_numstr += 1
        t_tm = str(time.strftime('%Y-%m-%d %H:%M:%S'))
        txt2 = self.set_tab_space(txt)

        txt = str('[%s] %s%8s%s %s' % (self.colorize_result(t_result), self.colsep, t_test, self.colsep, self.colorize_text(t_result,t_test,txt2)))
        txt3 = str('[%7s] %s%8s%s %s' % (t_result, self.colsep, t_test, self.colsep, txt2))
        llog = '%s %s%s' % (t_tm, self.colsep, txt3)

        if not self.log_show_testtype:
            txt = str('[%s] %s %s' % (self.colorize_result(t_result), self.colsep, self.colorize_text(t_result,t_test,txt2)))

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
                txt = '%s %s %s' % ( self.colorize_text(t_result,t_test,t_comment.ljust(self.col_comment_width)[0:self.col_comment_width]), self.colsep, txt)
            except UnicodeDecodeError:
                pass
            except TypeError:
                pass

        etm = self.elapsed_time_str()
        llog = '%s %s %s' % (etm, self.colsep, llog)

        if not self.log_hide_time:
            txt = '%s %s %s' % (etm, self.colsep, txt)

        llog = '%6s %s %s' % ("CHECK", self.colsep, llog)
        if self.show_test_type:
            txt = '%6s %s %s' % ("CHECK", self.colsep, txt)

        if not self.notimestamp:
            txt = "%s %s%s" % (t_tm, self.colsep, txt)

        if self.log_show_numline:
            txt = '%4s %s %s' % (self.log_numstr, self.colsep, txt)

        self.write_logfile(txt)
        self.log_list.append(llog)

        if self.printlog:
            print txt
            if self.log_flush:
                sys.stdout.flush()

    def print_actlog(self, t_result, t_act, txt, t_comment):
        self.log_numstr += 1
        t_tm = str(time.strftime('%Y-%m-%d %H:%M:%S'))
        txt2 = self.set_tab_space(txt)
        txt3 = str('[%7s] %s%8s%s %s' % (t_result, self.colsep, t_act, self.colsep, txt2))
        llog = '%s %s%s' % (t_tm, self.colsep, txt3)

        txt = str('[%7s] %s%8s%s %s' % (self.colorize_result(t_result), self.colsep, t_act, self.colsep, self.colorize_text(t_result,t_act, txt2)))

        if not self.log_show_testtype:
            txt = str('[%7s] %s %s' % (self.colorize_result(t_result), self.colsep, self.colorize_text(t_result,t_act,txt2)))

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
                txt = '%s %s %s' % (self.colorize_text(t_result,t_act,t_comment.ljust(self.col_comment_width)[0:self.col_comment_width]), self.colsep, txt)
            except UnicodeDecodeError:
                pass
            except TypeError:
                pass

        etm = self.elapsed_time_str()
        llog = '%s %s %s' % (etm, self.colsep, llog)
        if not self.log_hide_time:
            txt = '%s %s %s' % (etm, self.colsep, txt)

        llog = '%6s %s %s' % ('ACTION', self.colsep, llog)
        if self.show_test_type:
            txt = '%6s %s %s' % ('ACTION', self.colsep, txt)

        if not self.notimestamp:
            txt = '%s %s%s' % (t_tm, self.colsep, txt)

        if self.log_show_numline:
            txt = '%4s %s %s' % (self.log_numstr, self.colsep, txt)

        self.write_logfile(txt)
        self.log_list.append(llog)

        if self.printactlog:
            print txt
            if self.log_flush:
                sys.stdout.flush()

    def log(self, t_result, t_test, txt, t_comment, throw=False):

        try:
            if t_comment!=None and len(t_comment): 
                t_comment = unicode(t_comment, "UTF-8", errors='replace')
        except UnicodeDecodeError:
            pass
        except TypeError:
            pass

        if self.print_log is not None:
            self.print_log(t_result, t_test, txt, t_comment)

        if self.log_callback:
            self.log_callback(t_result, t_test, txt, t_comment, throw)

        if False == self.ignorefailed and True == throw:
            raise TestSuiteException(txt)

    def actlog(self, t_result, t_act, txt, t_comment, throw=False):

        try:
            if t_comment!=None and len(t_comment): 
                t_comment = unicode(t_comment, "UTF-8", errors='replace')
        except UnicodeDecodeError:
            pass
        except TypeError:
            pass

        if self.print_actlog is not None:
            self.print_actlog(t_result, t_act, txt, t_comment)

        if self.actlog_callback:
            self.actlog_callback(t_result, t_act, txt, t_comment, throw)

        if self.ignorefailed == False and throw == True:
            raise TestSuiteException(txt)

    def get_ui(self, cf):
        try:
            if cf == "" or cf is None:
                return None

            return self.ui_list[cf]

        except KeyError, ValueError:
            self.log(t_FAILED, '(get_ui): Unknown cf=\'%s\'' % cf, "", True)

        return None

    def getValue(self, s_id, ui=None):
        if ui is None:
            ui = self.default_ui

        return ui.getValue(s_id)

    def isTrue(self, s_id, t_out, t_check, t_comment, ui=None):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)

        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:
                if ui.getValue(s_id) == True:
                    self.log(t_PASSED, 'TRUE', '%s=true' % s_id, t_comment, False)
                    return True

                time.sleep(t_sleep)
                t_tick -= 1

            self.log(t_FAILED, 'TRUE', '%s!=true timeout=%d msec' % (s_id, t_out), t_comment, True)

        except UException, e:
            self.log(t_FAILED, 'TRUE', '(%s=true) error: %s' % (s_id, e.getError()), t_comment, True)

        return False

    def holdTrue(self, s_id, t_out, t_check, t_comment, ui=None):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)

        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:
                if ui.getValue(s_id) == False:
                    self.log(t_FAILED, 'TRUE', 'HOLD %s=true holdtime=%d msec' % (s_id, t_out), t_comment, True)
                    return False

                time.sleep(t_sleep)
                t_tick -= 1

            self.log(t_PASSED, 'TRUE', 'HOLD %s=true holdtime=%d' % (s_id, t_out), t_comment, False)
            return True

        except UException, e:
            self.log(t_FAILED, 'TRUE', 'HOLD (%s=true) error: %s' % (s_id, e.getError()), t_comment, True)

        return False

    def isFalse(self, s_id, t_out, t_check, t_comment, ui=None):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:

                if ui.getValue(s_id) == 0:
                    self.log(t_PASSED, 'FALSE', '%s=false' % s_id, t_comment, False)
                    return True

                time.sleep(t_sleep)
                t_tick -= 1

            self.log(t_FAILED, 'FALSE', '%s!=false timeout=%d msec' % (s_id, t_out), t_comment, True)

        except UException, e:
            self.log(t_FAILED, 'FALSE', '(%s=false) error: %s' % (s_id, e.getError()), t_comment, True)

        return False

    def holdFalse(self, s_id, t_out, t_check, t_comment, ui=None):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:

                if ui.getValue(s_id) == True:
                    self.log(t_FAILED, 'FALSE', 'HOLD %s!=false holdtime=%d msec' % (s_id, t_out), t_comment, True)
                    return False

                time.sleep(t_sleep)
                t_tick -= 1

            self.log(t_PASSED, 'FALSE', 'HOLD %s=false holdtime=%d msec' % s_id, t_comment, False)
            return True

        except UException, e:
            self.log(t_FAILED, 'FALSE', 'HOLD (%s=false) error: %s' % (s_id, e.getError()), t_comment, True)

        return False

    def isEqual(self, s_id, val, t_out, t_check, t_comment, ui=None):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        v1 = 0
        v2 = 0
        try:
            if self.log_flush:
                sys.stdout.flush()

            v = 0  # ui.getValue(s_id)
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = ui.getValue(s_id[0])
                    v2 = ui.getValue(s_id[1])
                    if v1 == v2:
                        self.log(t_PASSED, 'EQUAL', '%s(%d)=%s(%d)' % (s_id[0], v1, s_id[1], v2), t_comment, False)
                        return True
                else:
                    v = ui.getValue(s_id)
                    if v == val:
                        self.log(t_PASSED, 'EQUAL', '%s=%d' % (s_id, val), t_comment, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            if len(s_id) == 2:
                self.log(t_FAILED, 'EQUAL', '%s(%d)=%s(%d) timeout=%d msec' % (s_id[0], v1, s_id[1], v2, t_out), t_comment, True)
            else:
                self.log(t_FAILED, 'EQUAL', '%s=%d != %d timeout=%d msec' % (s_id, v, val, t_out), t_comment, True)

        except UException, e:
            if len(s_id) == 2:
                self.log(t_FAILED, 'EQUAL', '%s(%d)=%s(%d) error: %s' % (s_id[0], v1, s_id[1], v2, e.getError()), t_comment, True)
            else:
                self.log(t_FAILED, 'EQUAL', '(%s=%d) error: %s' % (s_id, val, e.getError()), t_comment, True)

        return False

    def holdEqual(self, s_id, val, t_out, t_check, t_comment, ui=None):

        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        v1 = 0
        v2 = 0
        try:
            if self.log_flush:
                sys.stdout.flush()

            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = ui.getValue(s_id[0])
                    v2 = ui.getValue(s_id[1])
                    if v1 != v2:
                        self.log(t_FAILED, 'EQUAL', 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out), t_comment,True)
                        return False
                else:
                    v = ui.getValue(s_id)
                    if v != val:
                        self.log(t_FAILED, 'EQUAL', 'HOLD %s=%d != %d holdtime=%d msec' % (s_id, v, val, t_out), t_comment,True)
                        return False

                time.sleep(t_sleep)
                t_tick -= 1

            if len(s_id) == 2:
                self.log(t_PASSED, 'EQUAL', 'HOLD %s(%d)=%s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out), t_comment, False)
            else:
                self.log(t_PASSED, 'EQUAL', 'HOLD %s=%d  holdtime=%d' % (s_id, val, t_out), t_comment, False)
            return True

        except UException, e:
            if len(s_id) == 2:
                self.log(t_FAILED, 'EQUAL', 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out), t_comment, True)
            else:
                self.log(t_FAILED, 'EQUAL', 'HOLD (%s=%d) error: %s' % (s_id, val, e.getError()), t_comment, True)

        return False

    def isNotEqual(self, s_id, val, t_out, t_check, t_comment, ui=None):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        v1 = 0
        v2 = 0

        try:
            if self.log_flush:
                sys.stdout.flush()

            v = 0  # ui.getValue(s_id)
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = ui.getValue(s_id[0])
                    v2 = ui.getValue(s_id[1])
                    if v1 != v2:
                        self.log(t_PASSED, 'NOTEQUAL', '%s(%d)!=%s(%d)' % (s_id[0], v1, s_id[1], v2), t_comment, False)
                        return True
                else:
                    v = ui.getValue(s_id)
                    if v != val:
                        self.log(t_PASSED, 'NOTEQUAL', '%s!=%d' % (s_id, val), t_comment, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            if len(s_id) == 2:
                self.log(t_FAILED, 'NOTEQUAL', '%s(%d) != %s(%d) timeout=%d msec' % (s_id[0], v1, s_id[1], v2, t_out), t_comment, True)
            else:
                self.log(t_FAILED, 'NOTEQUAL', '%s=%d != %d timeout=%d msec' % (s_id, v, val, t_out), t_comment, True)

        except UException, e:
            if len(s_id) == 2:
                self.log(t_FAILED, 'NOTEQUAL', '%s(%d)!=%s(%d) error: %s' % (s_id[0], v1, s_id[1], v2, e.getError()), t_comment, True)
            else:
                self.log(t_FAILED, 'NOTEQUAL', '(%s=%d) error: %s' % (s_id, val, e.getError()), t_comment, True)

        return False

    def holdNotEqual(self, s_id, val, t_out, t_check, t_comment, ui=None):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        v1 = 0
        v2 = 0

        try:
            if self.log_flush:
                sys.stdout.flush()

            v = 0  # ui.getValue(s_id)
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = ui.getValue(s_id[0])
                    v2 = ui.getValue(s_id[1])
                    if v1 == v2:
                        self.log(t_FAILED, 'NOTEQUAL', 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out), t_comment, True)
                        return False
                else:
                    v = ui.getValue(s_id)
                    if v == val:
                        self.log(t_FAILED, 'NOTEQUAL', 'HOLD %s=%d != %d holdtime=%d msec' % (s_id, v, val, t_out), t_comment, True)
                        return False

                time.sleep(t_sleep)
                t_tick -= 1

            if len(s_id) == 2:
                self.log(t_PASSED, 'NOTEQUAL', 'HOLD %s(%d)!=%s(%d) holdtime=%d' % (s_id[0], v1, s_id[1], v2, t_out), t_comment, False)
            else:
                self.log(t_PASSED, 'NOTEQUAL', 'HOLD %s!=%d holdtime=%d' % (s_id, val, t_out), t_comment, False)
            return True

        except UException, e:
            if len(s_id) == 2:
                self.log(t_FAILED, 'NOTEQUAL', 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out), t_comment, True)
            else:
                self.log(t_FAILED, 'NOTEQUAL', '(%s=%d) error: %s' % (s_id, val, e.getError()), t_comment, True)

        return False

    def isGreat(self, s_id, val, t_out, t_check, t_comment, ui=None, cond='>='):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        v = 0
        v1 = 0
        v2 = 0

        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:

                if len(s_id) == 2:
                    v1 = ui.getValue(s_id[0])
                    v2 = ui.getValue(s_id[1])
                    if (cond == '>=' and v1 >= v2) or (cond == '>' and v1 > v2):
                        self.log(t_PASSED, 'GREAT', '%s(%d) %s %s(%d)' % (s_id[0], v1, cond, s_id[1],v2), t_comment, False)
                        return True
                else:
                    v = ui.getValue(s_id)
                    if (cond == '>=' and v >= val) or (cond == '>' and v > val):
                        self.log(t_PASSED, 'GREAT', '%s=%s %s %d' % (s_id, v, cond, val), t_comment, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            if len(s_id) == 2:
                self.log(t_FAILED, 'GREAT', '%s(%d) not %s %s(%d) timeout=%d msec' % (s_id[0], v1, cond, s_id[1],v2, t_out), t_comment, True)
            else:
                self.log(t_FAILED, 'GREAT', '%s=%d not %s %d timeout=%d msec' % (s_id, v, cond, val, t_out), t_comment, True)

        except UException, e:
            if len(s_id) == 2:
                self.log(t_FAILED, 'GREAT', '%s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1],v2, e.getError()), t_comment, True)
            else:
                self.log(t_FAILED, 'GREAT', '(%s%s%d) error: %s' % (s_id, cond, val, e.getError()), t_comment, True)

        return False

    def holdGreat(self, s_id, val, t_out, t_check, t_comment, ui=None, cond='>='):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        v = val
        v1 = 0
        v2 = 0
        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = ui.getValue(s_id[0])
                    v2 = ui.getValue(s_id[1])
                    if (cond == '>=' and v1 < v2) or (cond == '>' and v1 <= v2):
                        self.log(t_FAILED, 'GREAT', 'HOLD %s(%d) not %s %s(%d) holdtime=%d msec' % (s_id[0], v1, cond, s_id[1],v2, t_out), t_comment, True)
                        return False
                else:
                    v = ui.getValue(s_id)
                    if (cond == '>=' and v < val) or (cond == '>' and v <= val):
                        self.log(t_FAILED, 'GREAT', 'HOLD %s=%d not %s %d holdtime=%d msec' % (s_id, v, cond, val, t_out), t_comment, True)
                        return False

                time.sleep(t_sleep)
                t_tick -= 1

            if len(s_id) == 2:
                self.log(t_PASSED, 'GREAT', 'HOLD %s(%d) %s %s(%d) holdtime=%d' % (s_id[0], v1, cond, s_id[1],v2, t_out), t_comment, False)
            else:
                self.log(t_PASSED, 'GREAT', 'HOLD %s=%s %s %d' % (s_id, v, cond, val), t_comment, False)
            return True

        except UException, e:
            if len(s_id) == 2:
                self.log(t_FAILED, 'GREAT', 'HOLD %s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1],v2, e.getError()), t_comment, True)
            else:
                self.log(t_FAILED, 'GREAT', 'HOLD (%s%s%d) error: %s' % (s_id, cond, val, e.getError()), t_comment, True)

        return False

    def isLess(self, s_id, val, t_out, t_check, t_comment, ui=None, cond='<='):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        v = 0
        v1 = 0
        v2 = 0
        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = ui.getValue(s_id[0])
                    v2 = ui.getValue(s_id[1])
                    if (cond == '<=' and v1 <= v2) or (cond == '<' and v1 < v2):
                        self.log(t_PASSED, 'LESS', '%s(%d) %s %s(%d)' % (s_id[0], v1, cond, s_id[1],v2), t_comment, False)
                        return True
                else:
                    v = ui.getValue(s_id)
                    if (cond == '<=' and v <= val) or (cond == '<' and v < val):
                        self.log(t_PASSED, 'LESS', '%s=%s %s %d' % (s_id, v, cond, val), t_comment, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            if len(s_id) == 2:
                self.log(t_FAILED, 'LESS', '%s(%d) not %s %s(%d) timeout=%d msec' % (s_id[0], v1, cond, s_id[1],v2,t_out), t_comment, True)
            else:
                self.log(t_FAILED, 'LESS', '%s=%d not %s %d timeout=%d msec' % (s_id, v, cond, val, t_out), t_comment, True)

        except UException, e:
            if len(s_id) == 2:
                self.log(t_FAILED, 'LESS', '%s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1],v2,e.getError()), t_comment, True)
            else:
                self.log(t_FAILED, 'LESS', '(%s%s%d) error: %s' % (s_id, cond, val, e.getError()), t_comment, True)

        return False

    def holdLess(self, s_id, val, t_out, t_check, t_comment, ui=None, cond='<='):
        if ui is None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick -= 1

        v = val
        v1 = 0
        v2 = 0
        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = ui.getValue(s_id[0])
                    v2 = ui.getValue(s_id[1])
                    if (cond == '<=' and v1 > v2) or (cond == '<' and v1 >= v2):
                        self.log(t_FAILED, 'LESS', '%s(%d) not %s %s(%d) holdtime=%d msec' % (s_id[0], v1, cond, s_id[1],v2,t_out), t_comment, True)
                        return False
                else:
                    v = ui.getValue(s_id)
                    if (cond == '<=' and v > val) or (cond == '<' and v >= val):
                        self.log(t_FAILED, 'LESS', '%s=%d not %s %d holdtime=%d msec' % (s_id, v, cond, val, t_out), t_comment, True)
                        return False

                time.sleep(t_sleep)
                t_tick -= 1

            if len(s_id) == 2:
                self.log(t_PASSED, 'LESS', 'HOLD  %s(%d) %s %s(%d)' % (s_id[0], v1, cond, s_id[1],v2), t_comment, False)
            else:
                self.log(t_PASSED, 'LESS', 'HOLD %s=%s %s %d' % (s_id, v, cond, val), t_comment, False)
            return True

        except UException, e:
            if len(s_id) == 2:
                self.log(t_FAILED, 'LESS', 'HOLD  %s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1],v2,e.getError()), t_comment, True)
            else:
                self.log(t_FAILED, 'LESS', 'HOLD (%s%s%d) error: %s' % (s_id, cond, val, e.getError()), t_comment, True)

        return False

    def msleep(self, msec):
        if self.log_flush:
            sys.stdout.flush()
        self.actlog(" ", 'SLEEP', 'sleep %d msec' % msec, "", False)
        time.sleep((msec / 1000.))

    def setValue(self, s_id, s_val, t_comment, ui=None):
        try:
            if ui is None:
                ui = self.default_ui

            ui.setValue(s_id, s_val)
            self.actlog(t_PASSED, 'SETVALUE', '%s=%d' % (s_id, s_val), t_comment, False)
            return True
        except UException, e:
            self.actlog(t_FAILED, 'SETVALUE', '(%s=%s) error: %s' % (s_id, s_val, e.getError()), t_comment, True)
        return False

    def runscript(self, script_name, silent=True):
        try:

            if self.log_flush:
                sys.stdout.flush()

            sout = None
            serr = None
            if silent:
                nul_f = open(os.devnull, 'w')
                sout = nul_f
                serr = nul_f

            ret = subprocess.call(script_name, shell=True, stdin=None, stdout=sout, stderr=serr)
            if ret:
                self.actlog(t_FAILED, 'SCRIPT', '%s' % script_name, False)
                return False

            self.actlog(t_PASSED, 'SCRIPT', '%s' % script_name, False)
            return True

        except UException, e:
            self.actlog(t_FAILED, 'SCRIPT', '\'%s\' error: %s' % (script_name, e.getError()), True)
        return False

    def get_check_info(self, node, ui=None):
        if node is None:
            return 'Unknown node'

        if ui is None:
            ui = self.default_ui

        res = ""

        s_id = None
        s_val = None

        tname = node.prop("test").upper()
        if tname != 'LINK' and tname != 'OUTLINK':
            clist = self.rcheck.findall(tname)
            if len(clist) == 1:
                tname = clist[0][1].upper()
                s_id = clist[0][0]
                s_val = to_int(clist[0][2])
            elif len(clist) > 1:
                tname = 'MULTICHECK'

        if tname == '=':
            s = ui.getIDinfo(s_id)
            res = "%s=%s timeout=%d" % (s[2], s_val, to_int(node.prop("timeout")))
        elif tname == '>' or tname == '>=':
            s = ui.getIDinfo(s_id)
            res = "%s %s %s timeout=%d" % (s[2], tname, s_val, to_int(node.prop("timeout")))
        elif tname == '<' or tname == '<=':
            s = ui.getIDinfo(s_id)
            res = "%s %s %s timeout=%d" % (s[2], tname, s_val, to_int(node.prop("timeout")))
        elif tname == 'MULTICHECK':
            res = "%s" % (node.prop("set"))
        elif tname == 'LINK':
            res = "LINK: link='%s'" % (node.prop("link"))
        elif tname == 'OUTLINK':
            res = "OUTLINK: file='%s' link='%s'" % (node.prop("file"), node.prop("link"))

        return res

    def get_action_info(self, node, ui=None):
        if node is None:
            return 'Unknown node'

        if ui is None:
            ui = self.default_ui
        res = ""
        tname = 'SET'
        if to_str(node.prop('msleep')) != '':
            tname = 'MSLEEP'
        elif to_str(node.prop('script')) != '':
            tname = 'SCRIPT'

        if tname == 'SET':
            res = '({0:>5s}): {1:s}'.format(tname.lower(), node.prop("set"))
        elif tname == 'MSLEEP':
            res = '(%5s): %s msec' % (tname.lower(), node.prop('msleep'))
        elif tname == 'SCRIPT':
            res = '(%5s): script=\'%s\'' % (tname.lower(), node.prop('script'))

        return res

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

