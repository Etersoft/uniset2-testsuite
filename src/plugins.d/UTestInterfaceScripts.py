#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess
from UTestInterface import *
import uniset2.UGlobal as uglobal


class UTestInterfaceScripts(UTestInterface):
    """
    Тестовый интерфейс основанный на вызове скриптов.

    ФОРМАТ ТЕСТА: <check test="testscript=VALUE" params="param1 param2 param3.." show_output="1".../>
    РЕЗУЛЬТАТ: В качестве результата скрипт должен вывести на экран (stdout) строку TEST_SCRIPT_RESULT: VALUE
    ОШИБКИ: Если код возврата !=0 считается что произошла ошибка! В случае успеха скрипт должен вернуть код возврата 0.

    Дополнительные параметры:
        show_output=1 - вывести на экран stdout..

    Глобальные конфигурационные параметры (секция <Config>):
      max_output_read="value" - максимальное количество первых байт читаемое из вывода скрипта, чтобы получить результат.
      По умолчанию: 1000
    """

    def __init__(self, **kwargs):
        """
        :param kwargs: параметры
        """
        UTestInterface.__init__(self, 'scripts', **kwargs)

        self.max_read = 1000

        if 'xmlConfNode' in kwargs:
            xmlConfNode = kwargs['xmlConfNode']
            if not xmlConfNode:
                raise TestSuiteValidateError("(scripts:init): Unknown confnode")

            m_read = uglobal.to_int(xmlConfNode.prop("max_output_read"))
            if m_read > 0:
                self.max_read = m_read

        self.re_result = re.compile(r'TEST_SCRIPT_RESULT: ([-]{0,}\d{1,})')

    @staticmethod
    def parse_name(name, context):
        """
        Разбор строки вида: <check test="scriptname=XXX" params="param1 param2 param3" .../>
        :param name: исходный параметр (по сути и есть наш scriptname)
        :param context:
        :return: [scriptname, parameters]
        """

        if 'xmlnode' in context:
            xmlnode = context['xmlnode']
            return [name, uglobal.to_str(xmlnode.prop("params"))]

        return [name, ""]

    def validate_configuration(self, context):
        return [True, ""]

    def validate_parameter(self, name, context):
        """

        :param name:  scriptname
        :param context: ...
        :return: [Result, errors]
        """
        err = []

        xmlnode = None
        if 'xmlnode' in context:
            xmlnode = context['xmlnode']

        scriptname, params = self.parse_name(name, context)

        if not scriptname:
            err.append("(scripts:validate): ERROR: Unknown scriptname for %s" % str(xmlnode))

        if not is_executable(scriptname):
            err.append("(scripts:validate): ERROR: '%s' not exist" % scriptname)

        if len(err) > 0:
            return [False, ', '.join(err)]

        return [True, ""]

    def get_value(self, name, context):

        xmlnode = None
        if 'xmlnode' in context:
            xmlnode = context['xmlnode']

        if not xmlnode:
            raise TestSuiteException("(scripts:get_value): Unknown xmlnode for '%s'" % name)

        scriptname, params = self.parse_name(name, context)

        if len(scriptname) == 0:
            raise TestSuiteException("(scripts:get_value): Unknown script name for '%s'" % name)

        test_env = None
        if 'environment' in context:
            test_env = context['environment']

        s_out = ''
        s_err = ''

        cmd = scriptname + " " + params

        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=test_env, close_fds=True,
                                 shell=True)

            s_out = p.stdout.read(self.max_read)
            s_err = p.stderr.read(self.max_read)

            retcode = p.wait()

            if retcode != 0:
                emessage = "SCRIPT RETCODE(%d) != 0. stderr: %s" % (retcode, s_err.replace("\n", " "))
                raise TestSuiteException("(scripts:get_value): %s" % emessage)

        except subprocess.CalledProcessError, e:
            raise TestSuiteException("(scripts:get_value): %s for %s" % (e.message, name))

        if xmlnode.prop("show_output"):
            print s_out

        ret = self.re_result.findall(s_out)
        if not ret or len(ret) == 0:
            return None

        lst = ret[0]
        if not lst or len(lst) < 1:
            return None

        return uglobal.to_int(lst)

    def set_value(self, name, value, context):
        raise TestSuiteException(
            "(scripts:set_value): Function 'set' is not supported. Use <action script='..'> for %s" % name)


def uts_create_from_args(**kwargs):
    """
    Создание интерфейса
    :param kwargs: именованные параметры
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceScripts(**kwargs)


def uts_create_from_xml(xmlConfNode):
    """
    Создание интерфейса
    :param xmlConfNode: xml-узел с настройками
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceScripts(xmlConfNode=xmlConfNode)


def uts_plugin_name():
    return "scripts"
