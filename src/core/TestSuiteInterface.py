#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import re
import os
import sys
import uniset2
from uniset2.pyUExceptions import *
from uniset2.UGlobal import *
from TestSuiteGlobal import *

# \todo может потом перейти на использование colorama
# import colorama as clr

TS_PROJECT_NAME = 'uniset2-testsuite'


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
        self.default_ui = None
        # self.params = uniset2.Params_inst()
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

        self.plugins = dict()

    @staticmethod
    def get_alias_name(cname):
        v = cname.strip().split('@')
        if len(v) > 1:
            return [v[0], v[1]]

        # если @ не указана, то испольузем имя без точки как alias
        s = v[0].split('.')
        return [s[0], v[0]]

    @staticmethod
    def get_plugins_dir():
        for p in sys.path:
            d = os.path.join(p, TS_PROJECT_NAME)
            if os.path.isdir(d):
                return os.path.join(d, 'plugins.d')

        return ''

    def load_plugins(self, pluginDir):

        if not os.path.isdir(pluginDir):
            raise TestSuiteException("(TestSuite::load_plugins): plugin directory '%s' not found " % pluginDir)

        sys.path.append(pluginDir)

        for name in os.listdir(pluginDir):

            if not name:
                continue

            fullname = os.path.join(pluginDir, name)
            if os.path.isfile(fullname):
                ext = os.path.splitext(name)
                if len(ext)>1 and ext[1] == '.py':
                    m = __import__(os.path.splitext(name)[0])
                    self.plugins[m.uts_plugin_name()] = m

    def plugins_count(self):
        return len(self.plugins)

    def is_iterface_exist(self, iname):
        return iname in self.plugins

    def iterfaces_as_str(self):
        return ','.join(self.plugins.keys())

    def init_uniset_interfaces(self, conflist):

        try:
            if len(conflist) == 0 or not conflist:
                return

            if conflist.__class__.__name__ != 'list':
                s = self.get_alias_name(conflist)
                if s[1] == "":
                    return

                self.default_ui = self.add_uniset_interface(s[1], s[0])
            else:
                # умолчательный config - первый в списке
                s = self.get_alias_name(conflist[0])
                self.default_ui = self.add_uniset_interface(s[1], s[0])
                for c in conflist:
                    s = self.get_alias_name(c)
                    if s[1] == "":
                        continue
                    self.add_uniset_interface(s[1], s[0])

        except UException, e:
            self.set_result(make_fail_result('(init_testsuite): ' + str(e.getError())), True)
            raise e

    def add_uniset_interface(self, xmlfile, alias, already_ignore=True):

        if to_str(xmlfile) == "":
            return

        if alias in self.ui_list:
            if not already_ignore:
                self.set_result(make_fail_result(
                    '(add_uniset_config): %s already added..(Ignore add \'%s@%s\')' % (alias, alias, xmlfile)), True)
                return None
            return self.ui_list[alias]

        if 'uniset' not in self.plugins:
            raise TestSuiteException("(TestSuite::add_uniset_config): not found uniset plugin")

        ui = self.plugins['uniset'].uts_create_from_args(confile=xmlfile)
        ui.set_ignore_nodes(self.ignore_nodes)
        self.ui_list[alias] = ui
        return ui

    def add_interface(self, xmlnode, already_ignore=True):

        alias = xmlnode.prop('alias')

        if alias in self.ui_list:
            if not already_ignore:
                self.set_result(make_fail_result('(add_interface): %s already added..Ignore add...' % alias), True)
                return None

            return self.ui_list[alias]

        itype = xmlnode.prop('type')
        if itype not in self.plugins:
            raise TestSuiteValidateError("(add_interface): not found plugin for '%s'" % itype)

        ui = self.plugins[itype].uts_create_from_xml(xmlnode)
        ui.set_ignore_nodes(self.ignore_nodes)
        self.ui_list[alias] = ui

        if to_int(xmlnode.prop("default")):
            self.set_default_ui(ui)

        return ui

    def remove_config(self, alias):
        if alias in self.ui_list:
            self.ui_list.pop(alias)

    def get_default_ui(self):
        return self.default_ui

    def set_default_ui(self, ui):
        self.default_ui = ui

    @staticmethod
    def getArgParam(param, defval=""):
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
        for k, v in edict.items():
            self.env[k] = v

    def make_environ_varname(self, varname):
        """
        Формирование имени переменной окружения с использованием заданного префикса
        :param varname: имя
        """
        return self.envPrefix + '_' + varname

    def set_ignore_nodes(self, state):
        self.ignore_nodes = state
        for key, ui in self.ui_list.items():
            ui.set_ignore_nodes(state)

    def set_supplier_id(self, sup_id):
        self.supplierID = sup_id

    def set_ignorefailed(self, state):
        self.ignorefailed = state

    def get_ignorefailed(self):
        return self.ignorefailed

    def is_check_scenario_mode(self):
        return self.checkScenarioMode

    def set_check_scenario_mode(self, state):
        self.checkScenarioMode = state

    def set_check_scenario_mode_ignore_failed(self, state):
        self.checkScenarioMode_ignorefailed = state

    def is_show_test_tree_mode(self):
        return self.showTestTreeMode

    def set_show_test_tree_mode(self, state):
        self.showTestTreeMode = state

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
                r.make_call_trace(results, call_limits)
            except Exception:
                pass

    def print_result_report(self, results):
        for r in self.reporters:
            try:
                r.make_report(results, self.is_check_scenario_mode())
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

    def finish_test_event(self):

        if self.is_show_test_tree_mode() or self.nrecur > 0:
            return

        for r in self.reporters:
            try:
                r.finish_test_event()
            except Exception:
                pass

    def set_result(self, item, throw=False):

        if self.print_log is not None:
            self.print_log(item)

        if self.is_check_scenario_mode() and self.checkScenarioMode_ignorefailed:
            return

        if False == self.ignorefailed and True == throw:
            raise TestSuiteException(item['text'], item=item)

    def set_action_result(self, act, throw=False):

        if self.print_actlog is not None:
            self.print_actlog(act)

        if self.is_check_scenario_mode() and self.checkScenarioMode_ignorefailed:
            return

        if self.ignorefailed == False and throw == True:
            raise TestSuiteException(act['text'], item=act)

    def get_ui(self, cf):
        try:
            if cf == "" or cf is None:
                return None

            return self.ui_list[cf]

        except KeyError, e:
            self.set_result(make_fail_result('(get_ui): Unknown config=\'%s\'' % cf, 'UI'), True)
        except ValueError, e:
            self.set_result(make_fail_result('(get_ui): Unknown config=\'%s\'' % cf, 'UI'), True)

        return None

    def validate_configuration(self):

        res_ok = True
        errors = []

        for k, ui in self.ui_list.items():
            if not hasattr(ui,'checked') or not ui.checked:
                ui.checked = True # защита от повторной проверки
                ok, err = ui.validate_configuration()
                if not ok:
                    errors.append(str(err))
                    res_ok = False

        err = ''
        if len(errors) > 0:
            err = '\n\t'.join(errors)

        return [res_ok, err]

    def get_value(self, s_id, ui):

        if self.is_check_scenario_mode():
            ret, err = ui.validate_parameter(s_id)
            if ret == False:
                raise TestSuiteValidateError(err)
            return 0

        return ui.get_value(s_id)

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
                if self.get_value(s_id, ui) == True or self.is_check_scenario_mode():
                    item['result'] = t_PASSED
                    item['text'] = '%s=true' % s_id
                    self.set_result(item, False)
                    return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['text'] = '%s!=true timeout=%d msec' % (s_id, t_out)
            item['faulty_sensor'] = s_id
            self.set_result(item, True)

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['text'] = '(%s=true) error: %s' % (s_id, e.getError())
            item['faulty_sensor'] = s_id
            self.set_result(item, True)

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
                if self.get_value(s_id, ui) == False and not self.is_check_scenario_mode():
                    item['result'] = t_FAILED
                    item['text'] = 'HOLD %s=true holdtime=%d msec' % (s_id, t_out)
                    item['faulty_sensor'] = s_id
                    self.set_result(item, True)
                    return False

                if self.is_check_scenario_mode():
                    break

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            item['text'] = 'HOLD %s=true holdtime=%d' % (s_id, t_out)
            self.set_result(item, False)
            return True

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['text'] = 'HOLD (%s=true) error: %s' % (s_id, e.getError())
            item['faulty_sensor'] = s_id
            self.set_result(item, True)

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

                if self.get_value(s_id, ui) == 0 or self.is_check_scenario_mode():
                    item['result'] = t_PASSED
                    item['text'] = '%s=false' % s_id
                    self.set_result(item, False)
                    return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['text'] = '%s!=false timeout=%d msec' % (s_id, t_out)
            item['faulty_sensor'] = s_id
            self.set_result(item, True)

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['text'] = '(%s=false) error: %s' % (s_id, e.getError())
            item['faulty_sensor'] = s_id
            self.set_result(item, True)

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

                if self.get_value(s_id, ui) == True and not self.is_check_scenario_mode():
                    item['result'] = t_FAILED
                    item['text'] = 'HOLD %s!=false holdtime=%d msec' % (s_id, t_out)
                    item['faulty_sensor'] = s_id
                    self.set_result(item, True)
                    return False

                if self.is_check_scenario_mode():
                    break

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            item['text'] = 'HOLD %s=false holdtime=%d msec' % s_id
            self.set_result(item, False)
            return True

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['text'] = 'HOLD (%s=false) error: %s' % (s_id, e.getError())
            item['faulty_sensor'] = s_id
            self.set_result(item, True)

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
                    v1 = self.get_value(s_id[0], ui)
                    v2 = self.get_value(s_id[1], ui)
                    if v1 == v2 or self.is_check_scenario_mode():
                        item['result'] = t_PASSED
                        item['text'] = '%s(%s)=%s(%s)' % (s_id[0], v1, s_id[1], v2)
                        self.set_result(item, False)
                        return True
                else:
                    v = self.get_value(s_id, ui)
                    if v == val or self.is_check_scenario_mode():
                        item['result'] = t_PASSED
                        item['text'] = '%s=%s' % (s_id, val)
                        self.set_result(item, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['text'] = '%s=%s' % (s_id, val)
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%s)=%s(%s) timeout=%s msec' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = '%s=%s != %s timeout=%s msec' % (s_id, v, val, t_out)

            self.set_result(item, True)

        except (UException, TestSuiteValidateError), e:
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%s)=%s(%s) error: %s' % (s_id[0], v1, s_id[1], v2, e.getError())
            else:
                item['text'] = '(%s=%s) error: %s' % (s_id, val, e.getError())
            item['result'] = t_FAILED

            self.set_result(item, True)

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
                    v1 = self.get_value(s_id[0], ui)
                    v2 = self.get_value(s_id[1], ui)
                    if v1 != v2 and not self.is_check_scenario_mode():
                        item['result'] = t_FAILED
                        item['text'] = 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
                        item['faulty_sensor'] = s_id
                        self.set_result(item, True)
                        return False
                else:
                    v1 = self.get_value(s_id, ui)
                    if v1 != val and not self.is_check_scenario_mode():
                        item['result'] = t_FAILED
                        item['text'] = 'HOLD %s=%d != %d holdtime=%d msec' % (s_id, v1, val, t_out)
                        item['faulty_sensor'] = s_id
                        self.set_result(item, True)
                        return False

                if self.is_check_scenario_mode():
                    break

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d)=%s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = 'HOLD %s=%d  holdtime=%d' % (s_id, val, t_out)

            self.set_result(item, False)
            return True

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = 'HOLD (%s=%d) error: %s' % (s_id, val, e.getError())

            self.set_result(item, True)

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
                    v1 = self.get_value(s_id[0], ui)
                    v2 = self.get_value(s_id[1], ui)
                    if v1 != v2 or self.is_check_scenario_mode():
                        item['result'] = t_PASSED
                        item['text'] = '%s(%d)!=%s(%d)' % (s_id[0], v1, s_id[1], v2)
                        self.set_result(item, False)
                        return True
                else:
                    v = self.get_value(s_id, ui)
                    if v != val or self.is_check_scenario_mode():
                        item['result'] = t_PASSED
                        item['text'] = '%s!=%d' % (s_id, val)
                        self.set_result(item, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d) != %s(%d) timeout=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = '%s=%d != %d timeout=%d msec' % (s_id, v, val, t_out)

            self.set_result(item, True)

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d)!=%s(%d) error: %s' % (s_id[0], v1, s_id[1], v2, e.getError())
            else:
                item['text'] = '(%s=%d) error: %s' % (s_id, val, e.getError())

            self.set_result(item, True)

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
                    v1 = self.get_value(s_id[0], ui)
                    v2 = self.get_value(s_id[1], ui)
                    if v1 == v2 and not self.is_check_scenario_mode():
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
                        self.set_result(item, True)
                        return False
                else:
                    v = self.get_value(s_id, ui)
                    if v == val and not self.is_check_scenario_mode():
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = 'HOLD %s=%d != %d holdtime=%d msec' % (s_id, v, val, t_out)
                        self.set_result(item, True)
                        return False

                if self.is_check_scenario_mode():
                    break

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d)!=%s(%d) holdtime=%d' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = 'HOLD %s!=%d holdtime=%d' % (s_id, val, t_out)

            self.set_result(item, False)
            return True

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d) != %s(%d) holdtime=%d msec' % (s_id[0], v1, s_id[1], v2, t_out)
            else:
                item['text'] = '(%s=%d) error: %s' % (s_id, val, e.getError())

            self.set_result(item, True)

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
                    v1 = self.get_value(s_id[0], ui)
                    v2 = self.get_value(s_id[1], ui)
                    if (cond == '>=' and v1 >= v2) or (cond == '>' and v1 > v2) or self.is_check_scenario_mode():
                        item['result'] = t_PASSED
                        item['text'] = '%s(%d) %s %s(%d)' % (s_id[0], v1, cond, s_id[1], v2)
                        self.set_result(item, False)
                        return True
                else:
                    v = self.get_value(s_id, ui)
                    if (cond == '>=' and v >= val) or (cond == '>' and v > val) or self.is_check_scenario_mode():
                        item['result'] = t_PASSED
                        item['text'] = '%s=%s %s %d' % (s_id, v, cond, val)
                        self.set_result(item, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d) not %s %s(%d) timeout=%d msec' % (s_id[0], v1, cond, s_id[1], v2, t_out)
            else:
                item['text'] = '%s=%d not %s %d timeout=%d msec' % (s_id, v, cond, val, t_out)

            self.set_result(item, True)

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1], v2, e.getError())
            else:
                item['text'] = '(%s%s%d) error: %s' % (s_id, cond, val, e.getError())

            self.set_result(item, True)

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
                    v1 = self.get_value(s_id[0], ui)
                    v2 = self.get_value(s_id[1], ui)
                    if self.is_check_scenario_mode() == False and (
                                (cond == '>=' and v1 < v2) or (cond == '>' and v1 <= v2)):
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = 'HOLD %s(%d) not %s %s(%d) holdtime=%d msec' % (
                            s_id[0], v1, cond, s_id[1], v2, t_out)
                        self.set_result(item, True)
                        return False
                else:
                    v = self.get_value(s_id, ui)
                    if self.is_check_scenario_mode() == False and (
                                (cond == '>=' and v < val) or (cond == '>' and v <= val)):
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = 'HOLD %s=%d not %s %d holdtime=%d msec' % (s_id, v, cond, val, t_out)
                        self.set_result(item, True)
                        return False

                if self.is_check_scenario_mode():
                    break

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d) %s %s(%d) holdtime=%d' % (s_id[0], v1, cond, s_id[1], v2, t_out)
            else:
                item['text'] = 'HOLD %s=%s %s %d' % (s_id, v, cond, val)

            self.set_result(item, False)
            return True

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = 'HOLD %s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1], v2, e.getError())
            else:
                item['text'] = 'HOLD (%s%s%d) error: %s' % (s_id, cond, val, e.getError())

            self.set_result(item, True)

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
                    v1 = self.get_value(s_id[0], ui)
                    v2 = self.get_value(s_id[1], ui)
                    if self.is_check_scenario_mode() or (cond == '<=' and v1 <= v2) or (cond == '<' and v1 < v2):
                        item['result'] = t_PASSED
                        item['text'] = '%s(%d) %s %s(%d)' % (s_id[0], v1, cond, s_id[1], v2)
                        self.set_result(item, False)
                        return True
                else:
                    v = self.get_value(s_id, ui)
                    if self.is_check_scenario_mode() or (cond == '<=' and v <= val) or (cond == '<' and v < val):
                        item['result'] = t_PASSED
                        item['text'] = '%s=%s %s %d' % (s_id, v, cond, val)
                        self.set_result(item, False)
                        return True

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d) not %s %s(%d) timeout=%d msec' % (s_id[0], v1, cond, s_id[1], v2, t_out)
            else:
                item['text'] = '%s=%d not %s %d timeout=%d msec' % (s_id, v, cond, val, t_out)

            self.set_result(item, True)

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = '%s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1], v2, e.getError())
            else:
                item['text'] = '(%s%s%d) error: %s' % (s_id, cond, val, e.getError())

            self.set_result(item, True)

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
                    v1 = self.get_value(s_id[0], ui)
                    v2 = self.get_value(s_id[1], ui)
                    if self.is_check_scenario_mode() == False and (
                                (cond == '<=' and v1 > v2) or (cond == '<' and v1 >= v2)):
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = '%s(%d) not %s %s(%d) holdtime=%d msec' % (s_id[0], v1, cond, s_id[1], v2, t_out)
                        self.set_result(item, True)
                        return False
                else:
                    v = self.get_value(s_id, ui)
                    if self.is_check_scenario_mode() == False and (
                                (cond == '<=' and v > val) or (cond == '<' and v >= val)):
                        item['result'] = t_FAILED
                        item['faulty_sensor'] = s_id
                        item['text'] = '%s=%d not %s %d holdtime=%d msec' % (s_id, v, cond, val, t_out)
                        self.set_result(item, True)
                        return False

                if self.is_check_scenario_mode():
                    break

                time.sleep(t_sleep)
                t_tick -= 1

            item['result'] = t_PASSED
            if len(s_id) == 2:
                item['text'] = 'HOLD  %s(%d) %s %s(%d)' % (s_id[0], v1, cond, s_id[1], v2)
            else:
                item['text'] = 'HOLD %s=%s %s %d' % (s_id, v, cond, val)

            self.set_result(item, False)
            return True

        except (UException, TestSuiteValidateError), e:
            item['result'] = t_FAILED
            item['faulty_sensor'] = s_id
            if len(s_id) == 2:
                item['text'] = 'HOLD  %s(%d)%s%s(%d) error: %s' % (s_id[0], v1, cond, s_id[1], v2, e.getError())
            else:
                item['text'] = 'HOLD (%s%s%d) error: %s' % (s_id, cond, val, e.getError())

            self.set_result(item, True)

        return False

    def msleep(self, msec, act):

        act['type'] = 'SLEEP'
        act['text'] = 'sleep %d msec' % msec
        act['result'] = t_PASSED
        self.set_action_result(act, False)

        if self.is_check_scenario_mode():
            return True

        time.sleep((msec / 1000.))
        return True

    def set_value(self, s_id, s_val, act, ui, throwIfFail=True):

        try:
            act['text'] = '%s=%d' % (s_id, s_val)
            act['type'] = 'SETVALUE'
            act['ui'] = ui

            if ui is None:
                ui = self.default_ui

            if self.is_check_scenario_mode():
                ret, err = ui.validate_parameter(s_id)
                if ret == False:
                    act['result'] = t_FAILED
                    act['text'] = err
                    act['faulty_sensor'] = s_id
                    raise TestSuiteValidateError(err)
            else:
                ui.set_value(s_id, s_val, self.supplierID)

            act['result'] = t_PASSED
            self.set_action_result(act, False)
            return True

        except (UException, TestSuiteValidateError), e:
            act['text'] = '(%s=%s) error: %s' % (s_id, s_val, e.getError())
            act['result'] = t_FAILED
            act['faulty_sensor'] = s_id
            self.set_action_result(act, throwIfFail)

        return False

    def runscript(self, script_name, act, silent=True, throwIfFailed=True):
        try:
            act['type'] = 'SCRIPT'
            act['text'] = '%s' % script_name

            if self.is_check_scenario_mode():
                act['result'] = t_PASSED
                script = ''
                if script_name:
                    script = script_name.split(' ')

                if len(script) > 0:
                    script = script[0]

                if is_executable(script):
                    act['result'] = t_PASSED
                    self.set_action_result(act, False)
                    return True

                fname = ''
                if 'filename' in act:
                    fname = act['filename']

                act['result'] = t_FAILED
                act['text'] = "'SCRIPT ERROR('%s'): '%s' not found" % (fname, script)
                self.set_action_result(act, throwIfFailed)
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
                self.set_action_result(act, throwIfFailed)
                # os.chdir(curdir)
                return False

            # os.chdir(curdir)
            act['result'] = t_PASSED
            self.set_action_result(act, False)
            return True

        except (UException, TestSuiteValidateError), e:
            act['result'] = t_FAILED
            act['text'] = '\'%s\' error: %s' % (script_name, e.getError())
            self.set_action_result(act, throwIfFailed)

        except Exception, e:
            act['result'] = t_FAILED
            act['text'] = '\'%s\' catch python exception: %s' % (script_name, e.message)
            self.set_action_result(act, throwIfFailed)

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
            s = ui.parse_id(s_id)
            res = "%s=%s timeout=%d" % (s[2], s_val, to_int(node.prop("timeout")))
        elif tname == '>' or tname == '>=':
            s = ui.parse_id(s_id)
            res = "%s %s %s timeout=%d" % (s[2], tname, s_val, to_int(node.prop("timeout")))
        elif tname == '<' or tname == '<=':
            s = ui.parse_id(s_id)
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
