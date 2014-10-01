#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import subprocess

import uniset2.UInterface

from TestSuiteGlobal import *


class TestSuiteInterface():
    def __init__(self):

        self.ignorefailed = False
        self.notimestamp = False
        self.log_callback = None
        self.actlog_callback = None
        self.show_test_type = False
        self.log_flush = False
        self.logfilename = ""
        self.colsep = ":"  # символ разделитель столбцов (по умолчанию)
        self.ui_list = dict()
        self.conf_list = dict()
        self.default_ui = None
        self.params = Params_inst()
        self.log_numstr = 0
        self.log_show_numstr = False
        self.ignore_nodes = False
        self.rcheck = re.compile(r"([\w@\ ]{1,})([!><]{0,}[=]{0,})([\d\ ]{1,})")

    def get_aliasname(self, cname):
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
                break;
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
            self.log(t_FAILED, "(init_testsuite): " + str(e.getError()), True)
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
            if already_ignore == False:
                self.log(t_FAILED,
                         "(add_uniset_config): %s already added..(Ignore add '%s@%s')" % (alias, alias, xmlfile), True)
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
            if already_ignore == False:
                self.log(t_FAILED,
                         "(add_modbus_config): %s already added..(Ignore add '%s@%s')" % (alias, alias, xmlfile), True)
                return None
            return self.ui_list[alias]

        ip, port = get_mbslave_param(mbslave)
        if ip == None:
            self.log(t_FAILED, "(add_modbus_config): Failed get ip:port!  mbslave='%s'" % (mbslave), True)
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
            if already_ignore == False:
                self.log(t_FAILED,
                         "(set_default_config): %s already added..(Ignore add '%s@%s')" % (alias, alias, xmlfile), True)
                return False

            ui = UInterface()
            ui.create_uniset_interface(xmlfile, self.params)
            self.default_ui = ui
            self.conf_list["default"] = xmlfile

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
                    break;

        return defval

    def getArgInt(self, param, defval=0):
        for i in range(0, len(sys.argv)):
            if sys.argv[i] == param:
                if i + 1 < len(sys.argv):
                    return to_int(strsys.argv[i + 1])
                else:
                    break;

        return defval

    def checkArgParam(self, param, defval=""):
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
        if trunc == True:
            logfile = open(self.logfilename, "w")
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

    def write_logfile(self, txt):
        if self.logfilename == "" or self.logfilename == None:
            return
        try:
            logfile = open(self.logfilename, "a")
            logfile.writelines(txt)
            logfile.writelines('\n')
            logfile.close()
        except IOError:
            pass

    def print_log(self, txt):

        self.log_numstr += 1

        if self.notimestamp == False:
            t_tm = str(time.strftime("%Y-%m-%d %H:%M:%S"))
            txt = "%s %s%s" % (t_tm, self.colsep, txt)

        if self.show_test_type:
            txt = "%6s %s %s" % ("CHECK", self.colsep, txt)

        if self.log_show_numstr:
            txt = "%4s %s %s" % (self.log_numstr, self.colsep, txt)

        self.write_logfile(txt)

        if self.printlog == True:
            print txt
            if self.log_flush:
                sys.stdout.flush()

    def print_actlog(self, txt):

        self.log_numstr += 1

        if self.notimestamp == False:
            t_tm = str(time.strftime("%Y-%m-%d %H:%M:%S"))
            txt = "%s %s%s" % (t_tm, self.colsep, txt)

        if self.show_test_type:
            txt = "%6s %s %s" % ("ACTION", self.colsep, txt)

        if self.log_show_numstr:
            txt = "%4s %s %s" % (self.log_numstr, self.colsep, txt)

        self.write_logfile(txt)

        if self.printactlog == True:
            print txt
            if self.log_flush:
                sys.stdout.flush()

    def log(self, t_result, t_test, txt, throw=False):
        txt1 = str("[%7s] %s%8s%s %s" % (t_result, self.colsep, t_test, self.colsep, txt))

        self.print_log(txt1)
        if self.log_callback:
            self.log_callback(t_result, t_test, txt, throw)

        if self.ignorefailed == False and throw == True:
            raise TestSuiteException(txt1)

    def actlog(self, t_result, t_act, txt, throw=False):
        txt1 = str("[%7s] %s%8s%s %s" % (t_result, self.colsep, t_act, self.colsep, txt))
        self.print_actlog(txt1)
        if self.actlog_callback:
            self.actlog_callback(t_result, t_test, txt, throw)

        if self.ignorefailed == False and throw == True:
            raise TestSuiteException(txt1)

    def get_ui(self, cf):
        try:
            if cf == "" or cf == None:
                return None

            return self.ui_list[cf]

        except KeyError, ValueError:
            self.log(t_FAILED, "(get_ui): Unknown cf='%s'" % cf, True)

        return None

    def getValue(self, s_id, ui=None):
        if ui == None:
            ui = self.default_ui

        return ui.getValue(s_id)

    def isTrue(self, s_id, t_out, t_check, ui=None):
        if ui == None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)

        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick = t_tick - 1

        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:
                if ui.getValue(s_id) == True:
                    self.log(t_PASSED, "TRUE", "%s = true" % s_id, False)
                    return True

                time.sleep(t_sleep)
                t_tick = t_tick - 1

            self.log(t_FAILED, "TRUE", "%s != true timeout=%d msec" % (s_id, t_out), True)

        except UException, e:
            self.log(t_FAILED, "TRUE", "(%s=true) error: %s" % (s_id, e.getError()), True)

        return False

    def isFalse(self, s_id, t_out, t_check, ui=None):
        if ui == None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick = t_tick - 1

        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:
                if ui.getValue(s_id) == False:
                    self.log(t_PASSED, "FALSE", "%s = false" % s_id, False)
                    return True

                time.sleep(t_sleep)
                t_tick = t_tick - 1

            self.log(t_FAILED, "FALSE", "%s != false timeout=%d msec" % (s_id, t_out), True)

        except UException, e:
            self.log(t_FAILED, "FALSE", "(%s=false) error: %s" % (s_id, e.getError()), True)

        return False

    def isEqual(self, s_id, val, t_out, t_check, ui=None):
        if ui == None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick = t_tick - 1

        try:
            if self.log_flush:
                sys.stdout.flush()

            v = 0  # ui.getValue(s_id)
            while t_tick >= 0:
                v = ui.getValue(s_id)
                if v == val:
                    self.log(t_PASSED, "EQUAL", "%s = %d" % (s_id, val), False)
                    return True

                time.sleep(t_sleep)
                t_tick = t_tick - 1

            self.log(t_FAILED, "EQUAL", "%s=%d != %d timeout=%d msec" % (s_id, v, val, t_out), True)

        except UException, e:
            self.log(t_FAILED, "EQUAL", "(%s=%d) error: %s" % (s_id, val, e.getError()), True)

        return False

    def isNotEqual(self, s_id, val, t_out, t_check, ui=None):
        if ui == None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick = t_tick - 1

        try:
            if self.log_flush:
                sys.stdout.flush()

            v = 0  # ui.getValue(s_id)
            while t_tick >= 0:
                v = ui.getValue(s_id)
                if v != val:
                    self.log(t_PASSED, "NOTEQUAL", "%s = %d" % (s_id, val), False)
                    return True

                time.sleep(t_sleep)
                t_tick = t_tick - 1

            self.log(t_FAILED, "NOTEQUAL", "%s=%d != %d timeout=%d msec" % (s_id, v, val, t_out), True)

        except UException, e:
            self.log(t_FAILED, "NOTEQUAL", "(%s=%d) error: %s" % (s_id, val, e.getError()), True)

        return False

    def isGreat(self, s_id, val, t_out, t_check, ui=None, cond='>='):
        if ui == None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick = t_tick - 1

        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:
                v = ui.getValue(s_id)
                if ( cond == '>=' and v >= val ) or ( cond == '>' and v > val ):
                    self.log(t_PASSED, "GREAT", "%s %s %d" % (s_id, cond, val), False)
                    return True

                time.sleep(t_sleep)
                t_tick = t_tick - 1

            self.log(t_FAILED, "GREAT", "%s=%d not %s %d timeout=%d msec" % (s_id, v, cond, val, t_out), True)

        except UException, e:
            self.log(t_FAILED, "GREAT", "(%s %s %d) error: %s" % (s_id, cond, val, e.getError()), True)

        return False

    def isLess(self, s_id, val, t_out, t_check, ui=None, cond='<='):
        if ui == None:
            ui = self.default_ui

        t_tick = round(t_out / t_check)
        t_sleep = (t_check / 1000.)
        # т.к. пришлось сделать
        # while t_tick >= 0
        # чтобы хоть раз тест проходил
        # то... надо делать -1, чтобы было правильное количество tick-ов
        # (т.к. ноль включается в цикл)
        if t_out > 0:
            t_tick = t_tick - 1

        try:
            if self.log_flush:
                sys.stdout.flush()
            while t_tick >= 0:
                v = ui.getValue(s_id)
                if ( cond == '<=' and v <= val ) or ( cond == '<' and v < val ):
                    self.log(t_PASSED, "LESS", "%s %s %d" % (s_id, cond, val), False)
                    return True

                time.sleep(t_sleep)
                t_tick = t_tick - 1

            self.log(t_FAILED, "LESS", "%s=%d not %s %d timeout=%d msec" % (s_id, v, cond, val, t_out), True)

        except UException, e:
            self.log(t_FAILED, "LESS", "(%s %s %d) error: %s" % (s_id, cond, val, e.getError()), True)

        return False

    def msleep(self, msec):
        if self.log_flush:
            sys.stdout.flush()
        self.actlog(" ", " ", "sleep %d msec" % msec, False)
        time.sleep((msec / 1000.))

    def setValue(self, s_id, s_val, ui=None):
        try:
            if ui == None:
                ui = self.default_ui

            ui.setValue(s_id, s_val)
            self.actlog(t_PASSED, "SETVALUE", "%s=%d" % (s_id, s_val), False)
            return True
        except UException, e:
            self.actlog(t_FAILED, "SETVALUE", "(%s=%s) error: %s" % (s_id, s_val, e.getError()), True)
        return False

    def runscript(self, script_name, silent=True):
        try:

            if self.log_flush:
                sys.stdout.flush()

            sout = None
            serr = None
            if silent == True:
                nul_f = open(os.devnull, 'w')
                sout = nul_f
                serr = nul_f

            ret = subprocess.call(script_name, shell=True, stdin=None, stdout=sout, stderr=serr)
            if ret:
                self.actlog(t_FAILED, "SCRIPT", "%s" % script_name, False)
                return False

            self.actlog(t_PASSED, "SCRIPT", "%s" % script_name, False)
            return True

        except UException, e:
            self.actlog(t_FAILED, "SCRIPT", "(%s=%s) error: %s" % (s_id, s_val, e.getError()), True)
        return False

    def get_check_info(self, node, ui=None):
        if node == None:
            return "Unknown node"

        if ui == None:
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
        if node == None:
            return "Unknown node"

        if ui == None:
            ui = self.default_ui
        res = ""
        tname = 'SET'
        if to_str(node.prop("msleep")) != '':
            tname = 'MSLEEP'
        elif to_str(node.prop("script")) != '':
            tname = 'SCRIPT'

        if tname == 'SET':
            res = "(%5s): %s" % (tname.lower(), node.prop("set"))
        elif tname == 'MSLEEP':
            res = "(%5s): %s msec" % (tname.lower(), node.prop("msleep"))
        elif tname == 'SCRIPT':
            res = "(%5s): script='%s'" % (tname.lower(), node.prop("script"))

        return res