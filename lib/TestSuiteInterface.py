#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uniset2
import subprocess

# \todo может потом перейти на использование colorama
# import colorama as clr

from UInterfaceSNMP import *
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
        self.ui_list = dict()
        self.conf_list = dict()
        self.default_ui = None
        self.params = Params_inst()
        self.ignore_nodes = False
        self.nrecur = 0
        self.supplierID = uniset2.DefaultSupplerID
        self.checkScenarioMode = False
        self.checkScenarioMode_ignorefailed = False
        self.showTestTreeMode = False
        self.reporters = list()

        self.rcheck = re.compile(r"([\w@\ :]+)([!><]*[=]*)([-\d\ ]+)")
        self.rcompare = re.compile(r"([\w@\ :]+)([!><]*[=]*)([\w@\ :]+)")

        self.env = os.environ.copy()
        self.envPrefix = "UNISET_TESTSUITE"

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
            self.setResult(make_fail_result('(init_testsuite): ' + str(e.getError())), True)
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
                self.setResult(make_fail_result(
                    '(add_uniset_config): %s already added..(Ignore add \'%s@%s\')' % (alias, alias, xmlfile)), True)
                return None
            return self.ui_list[alias]

        ui = UInterfaceUniSet(xmlfile, self.params)
        ui.set_ignore_nodes(self.ignore_nodes)
        self.ui_list[alias] = ui
        self.conf_list[alias] = xmlfile
        return ui

    def add_modbus_config(self, mbslave, alias, already_ignore=True):

        if alias in self.ui_list:
            if not already_ignore:
                self.setResult(make_fail_result(
                    '(add_modbus_config): %s already added..(Ignore add \'%s@%s\')' % (alias, alias, mbslave)), True)
                return None
            return self.ui_list[alias]

        ip, port = get_mbslave_param(mbslave)
        if ip is None:
            self.setResult(make_fail_result('(add_modbus_config): Failed get ip:port!  mbslave=\'%s\'' % (mbslave)),
                           True)
            return None

        ui = UInterfaceModbus(ip, port)
        self.ui_list[alias] = ui
        return ui

    def add_snmp_config(self, snmpConfile, alias, already_ignore=True):

        if alias in self.ui_list:
            if not already_ignore:
                self.setResult(make_fail_result(
                    '(add_snmp_config): %s already added..(Ignore add \'%s@%s\')' % (alias, alias, snmpConfile)), True)
                return None
            return self.ui_list[alias]

        try:
            ui = UInterfaceSNMP(snmpConfile)
            self.ui_list[alias] = ui
            return ui
        except UException, e:
            self.setResult(make_fail_result('(add_snmp_config): ERROR: %s' % e.getError()), True)
            return None

    def remove_config(self, alias):
        if alias in self.ui_list:
            self.ui_list.pop(alias)

    def set_default_config(self, xmlfile, already_ignore=True):

        if xmlfile in self.ui_list:
            if not already_ignore:
                self.setResult(make_fail_result('(set_default_config): %s already added..(Ignore add..)' % (xmlfile)),
                               True)
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

    def add_testsuite_environ_variable(self, varname, value):
        """
        Добавление testsuite-переменной окружения (т.е. с префиксом)
        :param varname: имя
        :param value: значение
        """
        self.env[self.make_environ_varname(varname)] = str(value)

    def set_user_envirion_variables(self, edict):
        """
        Добавление переменных окружения которые будут выставлены при запуске скриптов
        :param edict: словарь {VAR:VAL, VAR2:VAL2...}
        """
        for k,v in edict.items():
            self.env[k] = v

    def make_environ_varname(self,varname):
        """
        Формирование имени переменной окружения с использованием заданного префикса
        :param varname: имя
        """
        return self.envPrefix + '_' + varname;

    def set_ignore_nodes(self, state):
        self.ignore_nodes = state
        for key, ui in self.ui_list.items():
            ui.set_ignore_nodes(state)

    def set_supplier_id(self, supID):
        self.supplierID = supID

    def set_ignorefailed(self, state):
        self.ignorefailed = state

    def get_ignorefailed(self):
        return self.ignorefailed

    def isCheckScenarioMode(self):
        return self.checkScenarioMode

    def set_check_scenario_mode(self, set):
        self.checkScenarioMode = set

    def set_check_scenario_mode_ignore_failed(self, set):
        self.checkScenarioMode_ignorefailed = set

    def isShowTestTreeMode(self):
        return self.showTestTreeMode

    def set_show_test_tree_mode(self, set):
        self.showTestTreeMode = set

    def add_repoter(self, reporter):
        self.reporters.append(reporter)

    def start_tests(self):
        tm = time.time()
        for r in self.reporters:
            try:
                r.start_tests(tm)
            except Exception:
                pass

    def finish_tests(self):
        tm = time.time()
        for r in self.reporters:
            try:
                r.finish_tests(tm)
            except Exception:
                pass

    def print_call_trace(self, results, call_limits):
        for r in self.reporters:
            try:
                r.makeCallTrace(results, call_limits)
            except Exception:
                pass

    def print_result_report(self, results):
        for r in self.reporters:
            try:
                r.makeReport(results, self.isCheckScenarioMode())
            except Exception:
                pass

    def print_log(self, item):
        for r in self.reporters:
            try:
                r.print_log(item)
            except Exception:
                pass

    def print_actlog(self, act):

        for r in self.reporters:
            try:
                r.print_actlog(act)
            except Exception:
                pass

    def setResult(self, item, throw=False):

        if self.print_log is not None:
            self.print_log(item)

        if self.isCheckScenarioMode() and self.checkScenarioMode_ignorefailed:
            return

        if False == self.ignorefailed and True == throw:
            raise TestSuiteException(item['text'], item=item)

    def setActionResult(self, act, throw=False):

        if self.print_actlog is not None:
            self.print_actlog(act)

        if self.isCheckScenarioMode() and self.checkScenarioMode_ignorefailed:
            return

        if self.ignorefailed == False and throw == True:
            raise TestSuiteException(act['text'], item=act)

    def get_ui(self, cf):
        try:
            if cf == "" or cf is None:
                return None

            return self.ui_list[cf]

        except KeyError, e:
            self.setResult(make_fail_result('(get_ui): Unknown cf=\'%s\'' % cf, 'UI'), True)
        except ValueError, e:
            self.setResult(make_fail_result('(get_ui): Unknown cf=\'%s\'' % cf, 'UI'), True)

        return None

    def getValue(self, s_id, ui):

        if self.isCheckScenarioMode():
            ret, err = ui.validateParam(s_id)
            if ret == False:
                raise UValidateError(err)  # raise TestSuiteException(err)
            return 0

        return ui.getValue(s_id)

    def isTrue(self, s_id, t_out, t_check, item, ui):

        item['type'] = 'TRUE'
        item['ui'] = ui

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
            while t_tick >= 0:
                if self.getValue(s_id, ui) == True or self.isCheckScenarioMode():
                    item['result'] = t_PASSED
                    item['text'] = '%s=true' % s_id
                    self.setResult(item, False)
                    return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['text'] = '%s!=true timeout=%d msec' % (s_id, t_out)
            item['faulty_sensor'] = s_id
            self.setResult(item, True)

        except UException, e:
            item['result'] = t_FAILED
            item['text'] = '(%s=true) error: %s' % (s_id, e.getError())
            item['faulty_sensor'] = s_id
            self.setResult(item, True)

        return False

    def holdTrue(self, s_id, t_out, t_check, item, ui):

        item['type'] = 'TRUE'
        item['ui'] = ui
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
            while t_tick >= 0:
                if self.getValue(s_id, ui) == False or self.isCheckScenarioMode():
                    item['result'] = t_FAILED
                    item['text'] = 'HOLD %s=true holdtime=%d msec' % (s_id, t_out)
                    item['faulty_sensor'] = s_id
                    self.setResult(item, True)
                    return False

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            item['text'] = 'HOLD %s=true holdtime=%d' % (s_id, t_out)
            self.setResult(item, False)
            return True

        except UException, e:
            item['result'] = t_FAILED
            item['text'] = 'HOLD (%s=true) error: %s' % (s_id, e.getError())
            item['faulty_sensor'] = s_id
            self.setResult(item, True)

        return False

    def isFalse(self, s_id, t_out, t_check, item, ui):

        item['type'] = 'FALSE'
        item['ui'] = ui

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
            while t_tick >= 0:

                if self.getValue(s_id, ui) == 0 or self.isCheckScenarioMode():
                    item['result'] = t_PASSED
                    item['text'] = '%s=false' % s_id
                    self.setResult(item, False)
                    return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['text'] = '%s!=false timeout=%d msec' % (s_id, t_out)
            item['faulty_sensor'] = s_id
            self.setResult(item, True)

        except UException, e:
            item['result'] = t_FAILED
            item['text'] = '(%s=false) error: %s' % (s_id, e.getError())
            item['faulty_sensor'] = s_id
            self.setResult(item, True)

        return False

    def holdFalse(self, s_id, t_out, t_check, item, ui):

        item['type'] = 'FALSE'
        item['ui'] = ui
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
            while t_tick >= 0:

                if self.getValue(s_id, ui) == True and self.isCheckScenarioMode() == False:
                    item['result'] = t_FAILED
                    item['text'] = 'HOLD %s!=false holdtime=%d msec' % (s_id, t_out)
                    item['faulty_sensor'] = s_id
                    self.setResult(item, True)
                    return False

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            item['text'] = 'HOLD %s=false holdtime=%d msec' % s_id
            self.setResult(item, False)
            return True

        except UException, e:
            item['result'] = t_FAILED
            item['text'] = 'HOLD (%s=false) error: %s' % (s_id, e.getError())
            item['faulty_sensor'] = s_id
            self.setResult(item, True)

        return False

    def isEqual(self, s_id, val, t_out, t_check, item, ui):

        item['type'] = 'EQUAL'
        item['ui'] = ui
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
            v = 0  # ui.getValue(s_id)
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = self.getValue(s_id[0], ui)
                    v2 = self.getValue(s_id[1], ui)
                    if v1 == v2 or self.isCheckScenarioMode():
                        item['result'] = t_PASSED
                        item['text'] = '%s(%d)=%s(%d)' % (s_id[0], v1, s_id[1], v2)
                        self.setResult(item, False)
                        return True
                else:
                    v = self.getValue(s_id, ui)
                    if v == val or self.isCheckScenarioMode():
                        item['result'] = t_PASSED
                        item['text'] = '%s=%d' % (s_id, val)
                        self.setResult(item, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['text'] = '%s=%d' % (s_id, val)
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d)=%s(%d) timeout=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = '%s=%d != %d timeout=%d msec' % (s_id, v, val, t_out)

            self.setResult(item, True)

        except UException, e:
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d)=%s(%d) error: %s' % (s_id[0], v1, s_id[1], v2, e.getError())
            else:
                item['text'] = '(%s=%d) error: %s' % (s_id, val, e.getError())
            item['result'] = t_FAILED

            self.setResult(item, True)

        return False

    def holdEqual(self, s_id, val, t_out, t_check, item, ui):

        item['type'] = 'EQUAL'
        item['ui'] = ui
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
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = self.getValue(s_id[0], ui)
                    v2 = self.getValue(s_id[1], ui)
                    if v1 != v2 and not self.isCheckScenarioMode():
                        item['result'] = t_FAILED
                        item['text'] = 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
                        item['faulty_sensor'] = s_id
                        self.setResult(item, True)
                        return False
                else:
                    v1 = self.getValue(s_id, ui)
                    if v1 != val and not self.isCheckScenarioMode():
                        item['result'] = t_FAILED
                        item['text'] = 'HOLD %s=%d != %d holdtime=%d msec' % (s_id, v1, val, t_out)
                        item['faulty_sensor'] = s_id
                        self.setResult(item, True)
                        return False

                if self.isCheckScenarioMode():
                    break

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d)=%s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = 'HOLD %s=%d  holdtime=%d' % (s_id, val, t_out)

            self.setResult(item, False)
            return True

        except UException, e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = 'HOLD (%s=%d) error: %s' % (s_id, val, e.getError())

            self.setResult(item, True)

        return False

    def isNotEqual(self, s_id, val, t_out, t_check, item, ui):

        item['type'] = 'NOTEQUAL'
        item['ui'] = ui

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

            v = 0  # ui.getValue(s_id)
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = self.getValue(s_id[0], ui)
                    v2 = self.getValue(s_id[1], ui)
                    if v1 != v2 or self.isCheckScenarioMode():
                        item['result'] = t_PASSED
                        item['text'] = '%s(%d)!=%s(%d)' % (s_id[0], v1, s_id[1], v2)
                        self.setResult(item, False)
                        return True
                else:
                    v = self.getValue(s_id, ui)
                    if v != val or self.isCheckScenarioMode():
                        item['result'] = t_PASSED
                        item['text'] = '%s!=%d' % (s_id, val)
                        self.setResult(item, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d) != %s(%d) timeout=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = '%s=%d != %d timeout=%d msec' % (s_id, v, val, t_out)

            self.setResult(item, True)

        except UException, e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d)!=%s(%d) error: %s' % (s_id[0], v1, s_id[1], v2, e.getError())
            else:
                item['text'] = '(%s=%d) error: %s' % (s_id, val, e.getError())

            self.setResult(item, True)

        return False

    def holdNotEqual(self, s_id, val, t_out, t_check, item, ui):

        item['type'] = 'NOTEQUAL'
        item['ui'] = ui

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
            v = 0  # ui.getValue(s_id)
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = self.getValue(s_id[0], ui)
                    v2 = self.getValue(s_id[1], ui)
                    if v1 == v2 and not self.isCheckScenarioMode():
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
                        self.setResult(item, True)
                        return False
                else:
                    v = self.getValue(s_id, ui)
                    if v == val and not self.isCheckScenarioMode():
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = 'HOLD %s=%d != %d holdtime=%d msec' % (s_id, v, val, t_out)
                        self.setResult(item, True)
                        return False

                if self.isCheckScenarioMode():
                    break

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d)!=%s(%d) holdtime=%d' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = 'HOLD %s!=%d holdtime=%d' % (s_id, val, t_out)

            self.setResult(item, False)
            return True

        except UException, e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = '(%s=%d) error: %s' % (s_id, val, e.getError())

            self.setResult(item, True)

        return False

    def isGreat(self, s_id, val, t_out, t_check, item, ui, cond='>='):

        item['type'] = 'GREAT'
        item['ui'] = ui
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
            while t_tick >= 0:

                if len(s_id) == 2:
                    v1 = self.getValue(s_id[0], ui)
                    v2 = self.getValue(s_id[1], ui)
                    if (cond == '>=' and v1 >= v2) or (cond == '>' and v1 > v2) or self.isCheckScenarioMode():
                        item['result'] = t_PASSED
                        item['text'] = '%s(%d) %s %s(%d)' % (s_id[0], v1, cond, s_id[1], v2)
                        self.setResult(item, False)
                        return True
                else:
                    v = self.getValue(s_id, ui)
                    if (cond == '>=' and v >= val) or (cond == '>' and v > val) or self.isCheckScenarioMode():
                        item['result'] = t_PASSED
                        item['text'] = '%s=%s %s %d' % (s_id, v, cond, val)
                        self.setResult(item, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d) not %s %s(%d) timeout=%d msec' % (s_id[0], v1, cond, s_id[1], v2, t_out)
            else:
                item['text'] = '%s=%d not %s %d timeout=%d msec' % (s_id, v, cond, val, t_out)

            self.setResult(item, True)

        except UException, e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1], v2, e.getError())
            else:
                item['text'] = '(%s%s%d) error: %s' % (s_id, cond, val, e.getError())

            self.setResult(item, True)

        return False

    def holdGreat(self, s_id, val, t_out, t_check, item, ui, cond='>='):

        item['type'] = 'GREAT'
        item['ui'] = ui
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
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = self.getValue(s_id[0], ui)
                    v2 = self.getValue(s_id[1], ui)
                    if self.isCheckScenarioMode() == False and (
                                (cond == '>=' and v1 < v2) or (cond == '>' and v1 <= v2)):
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = 'HOLD %s(%d) not %s %s(%d) holdtime=%d msec' % (
                            s_id[0], v1, cond, s_id[1], v2, t_out)
                        self.setResult(item, True)
                        return False
                else:
                    v = self.getValue(s_id, ui)
                    if self.isCheckScenarioMode() == False and (
                                (cond == '>=' and v < val) or (cond == '>' and v <= val)):
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = 'HOLD %s=%d not %s %d holdtime=%d msec' % (s_id, v, cond, val, t_out)
                        self.setResult(item, True)
                        return False

                if self.isCheckScenarioMode():
                    break

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d) %s %s(%d) holdtime=%d' % (s_id[0], v1, cond, s_id[1], v2, t_out)
            else:
                item['text'] = 'HOLD %s=%s %s %d' % (s_id, v, cond, val)

            self.setResult(item, False)
            return True

        except UException, e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1], v2, e.getError())
            else:
                item['text'] = 'HOLD (%s%s%d) error: %s' % (s_id, cond, val, e.getError())

            self.setResult(item, True)

        return False

    def isLess(self, s_id, val, t_out, t_check, item, ui, cond='<='):

        item['type'] = 'LESS'
        item['ui'] = ui
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
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = self.getValue(s_id[0], ui)
                    v2 = self.getValue(s_id[1], ui)
                    if self.isCheckScenarioMode() or (cond == '<=' and v1 <= v2) or (cond == '<' and v1 < v2):
                        item['result'] = t_PASSED
                        item['text'] = '%s(%d) %s %s(%d)' % (s_id[0], v1, cond, s_id[1], v2)
                        self.setResult(item, False)
                        return True
                else:
                    v = self.getValue(s_id, ui)
                    if self.isCheckScenarioMode() or (cond == '<=' and v <= val) or (cond == '<' and v < val):
                        item['result'] = t_PASSED
                        item['text'] = '%s=%s %s %d' % (s_id, v, cond, val)
                        self.setResult(item, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d) not %s %s(%d) timeout=%d msec' % (s_id[0], v1, cond, s_id[1], v2, t_out)
            else:
                item['text'] = '%s=%d not %s %d timeout=%d msec' % (s_id, v, cond, val, t_out)

            self.setResult(item, True)

        except UException, e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1], v2, e.getError())
            else:
                item['text'] = '(%s%s%d) error: %s' % (s_id, cond, val, e.getError())

            self.setResult(item, True)

        return False

    def holdLess(self, s_id, val, t_out, t_check, item, ui, cond='<='):

        item['type'] = 'LESS'
        item['ui'] = ui
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
            while t_tick >= 0:
                if len(s_id) == 2:
                    v1 = self.getValue(s_id[0], ui)
                    v2 = self.getValue(s_id[1], ui)
                    if self.isCheckScenarioMode() == False and (
                                (cond == '<=' and v1 > v2) or (cond == '<' and v1 >= v2)):
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = '%s(%d) not %s %s(%d) holdtime=%d msec' % (s_id[0], v1, cond, s_id[1], v2, t_out)
                        self.setResult(item, True)
                        return False
                else:
                    v = self.getValue(s_id, ui)
                    if self.isCheckScenarioMode() == False and (
                                (cond == '<=' and v > val) or (cond == '<' and v >= val)):
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = '%s=%d not %s %d holdtime=%d msec' % (s_id, v, cond, val, t_out)
                        self.setResult(item, True)
                        return False

                if self.isCheckScenarioMode():
                    break

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            if len(s_id) == 2:
                item['text'] = 'HOLD  %s(%d) %s %s(%d)' % (s_id[0], v1, cond, s_id[1], v2)
            else:
                item['text'] = 'HOLD %s=%s %s %d' % (s_id, v, cond, val)

            self.setResult(item, False)
            return True

        except UException, e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = 'HOLD  %s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1], v2, e.getError())
            else:
                item['text'] = 'HOLD (%s%s%d) error: %s' % (s_id, cond, val, e.getError())

            self.setResult(item, True)

        return False

    def msleep(self, msec, act):

        act['type'] = 'SLEEP'
        act['text'] = 'sleep %d msec' % msec
        act['result'] = t_PASSED
        self.setActionResult(act, False)

        if self.isCheckScenarioMode():
            return True

        time.sleep((msec / 1000.))
        return True

    def setValue(self, s_id, s_val, act, ui, throwIfFail=True):

        try:
            act['text'] = '%s=%d' % (s_id, s_val)
            act['type'] = 'SETVALUE'
            act['ui'] = ui

            if ui is None:
                ui = self.default_ui

            if self.isCheckScenarioMode():
                ret, err = ui.validateParam(s_id)
                if ret == False:
                    act['result'] = t_FAILED
                    act['text'] = err
                    act['faulty_sensor'] = s_id
                    raise UValidateError(err)  # TestSuiteException(err,-1,act)
            else:
                ui.setValue(s_id, s_val, self.supplierID)

            act['result'] = t_PASSED
            self.setActionResult(act, False)
            return True

        except UException, e:
            act['text'] = '(%s=%s) error: %s' % (s_id, s_val, e.getError())
            act['result'] = t_FAILED
            act['faulty_sensor'] = s_id
            self.setActionResult(act, throwIfFail)

        return False

    def runscript(self, script_name, act, silent=True, throwIfFailed=True):
        try:
            act['type'] = 'SCRIPT'
            act['text'] = '%s' % script_name

            if self.isCheckScenarioMode():
                act['result'] = t_PASSED
                script = ''
                if script_name:
                    script = script_name.split(' ')

                if len(script) > 0:
                    script = script[0]

                if is_executable(script):
                    act['result'] = t_PASSED
                    self.setActionResult(act, False)
                    return True

                fname = ''
                if 'filename' in act:
                    fname = act['filename']

                act['result'] = t_FAILED
                act['text'] = "'SCRIPT ERROR('%s'): '%s' not found" % (fname, script)
                self.setActionResult(act, throwIfFailed)
                return False

            sout = None
            serr = None
            if silent:
                nul_f = open(os.devnull, 'w')
                sout = nul_f
                serr = nul_f

            # смена каталога на тот, где запускается скрипт..
            # curdir = os.getcwd()
            # script_path = os.dirname(script_name)
            # if script_path:
            #     os.chdir(script_path)

            ret = subprocess.call(script_name, shell=True, stdin=None, stdout=sout, stderr=serr, env=self.env)
            if ret:
                act['result'] = t_FAILED
                self.setActionResult(act, throwIfFailed)
                # os.chdir(curdir)
                return False

            # os.chdir(curdir)
            act['result'] = t_PASSED
            self.setActionResult(act, False)
            return True

        except uniset2.pyUExceptions.UException, e:
            act['result'] = t_FAILED
            act['text'] = '\'%s\' error: %s' % (script_name, e.getError())
            self.setActionResult(act, throwIfFailed)

        except Exception, e:
            act['result'] = t_FAILED
            act['text'] = '\'%s\' catch python exception..' % (script_name)
            self.setActionResult(act, throwIfFailed)

        return False

    def get_check_info(self, node, ui):
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
