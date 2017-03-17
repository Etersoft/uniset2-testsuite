#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

sys.path.append("../")

import uniset2
from uniset2.UGlobal import *
from uniset2.pyUExceptions import UException
from uniset2.pyUConnector import *
from UTestInterface import *
from TestSuiteGlobal import TestSuiteException, TestSuiteValidateError


class UTestInterfaceUniSet(UTestInterface):
    def __init__(self, **kwargs):
        UTestInterface.__init__(self, 'uniset', **kwargs)

        self.supplierID = DefaultID

        # Проверяем создание на основе xmlConfNode
        xmlfile = None

        if 'xmlConfNode' in kwargs:
            xmlConfNode = kwargs['xmlConfNode']
            xmlfile = xmlConfNode.prop('confile')
            if not xmlfile:
                raise TestSuiteValidateError("(uniset:init): Not found xmlfile='' in %s" % str(xmlConfNode))

            if xmlConfNode.prop('supplierID'):
                self.supplierID = xmlConfNode.prop('supplierID')
        # Проверяем создание на основе 'confile'
        elif 'confile' in kwargs:
            xmlfile = kwargs['confile']
            if not xmlfile:
                raise TestSuiteValidateError("(uniset:init): Unknown xmlfile")

        if not xmlfile:
            raise TestSuiteValidateError("(uniset:init): Unknown xmlfile")

        if 'suplierID' in kwargs:
            self.supplierID = kwargs['suplierID']

        params = uniset2.Params_inst()

        for i in range(0, len(sys.argv)):
            if i >= Params.max:
                break

            # пропускаем параметры типа --confile
            if sys.argv[i] == '--confile':
                continue

            if i != 0 and sys.argv[i - 1] == '--confile':
                continue

            params.add(sys.argv[i])

        try:
            self.ui = UConnector(params, xmlfile)
        except UException, e:
            raise TestSuiteValidateError("(uniset:init): ERR: %s " % e.getError())

    def get_conf_filename(self):
        return self.ui.getConfFileName()

    def parseID(self, name):
        return to_sid(name, self.ui)

    def validate_configuration(self, context):
        # todo Реализовать функцию проверки конфигурации
        return [True, ""]

    def validate_parameter(self, name, context):

        try:
            s = self.parseID(name)
            if s[0] == DefaultID:
                return [False, "(uniset): Unknown ID for '%s'" % str(name)]

            # id@node
            fullname = s[2]
            v = fullname.split('@')

            # если задан узел но его ID не найден
            if len(v) > 1 and v[1] and s[1] == DefaultID:
                return [False, "(uniset): Unknown ID for node '%s' in '%s'" % (v[1], str(name))]

            return [True, ""]

        except UException, e:
            return [False, "%s" % e.getError()]

    def get_value(self, name, context):

        try:
            s = self.parseID(name)
            if self.ignore_nodes:
                s[1] = DefaultID

            return self.ui.getValue(s[0], s[1])

        except UException, e:
            raise TestSuiteException(e.getError())

    def set_value(self, name, value, context):
        try:
            s = self.parseID(name)
            if self.ignore_nodes:
                s[1] = DefaultID

            self.ui.setValue(s[0], value, s[1], self.supplierID)
            return

        except UException, e:
            raise TestSuiteException(e.getError())

    def getConfFileName(self):
        return self.ui.getConfFileName()

    def getShortName(self, s_node):
        return self.ui.getShortName(s_node)

    def getNodeID(self, s_node):
        return self.ui.getNodeID(s_node)

    def getSensorID(self, s_name):
        return self.ui.getSensorID(s_name)

    def getObjectID(self, o_name):
        return self.ui.getObjectID(o_name)

    def getObjectInfo(self, o_name, params=""):
        """
        get information from object
        :param o_name: [id | name@node | id@node]
        :param params: user parameters for getObjectInfo function
        :return: string
        """

        s = self.parseID(o_name)
        return self.ui.getObjectInfo(s[0], params, s[1])

    def getTimeChange(self, o_name):
        """
        :param o_name: [id | name@node | id@node]
        :return: UTypes::ShortIOInfo
        """

        s = self.parseID(o_name)
        return self.ui.getTimeChange(s[0], s[1])

    def apiRequest(self, o_name, query=""):
        """
        call REST API for object
        :param o_name: [id | name@node | id@node]
        :param query: http query. example: /api/version/query_for_object?params или просто query_for_object?params
        :return: string [The default response format - json].
        """
        s = self.parseID(o_name)
        return self.ui.apiRequest(s[0], query, s[1])


def uts_plugin_name():
    return "uniset"


def uts_create_from_args(**kwargs):
    """
    Создание интерфейса
    :param kwargs: именованные параметры
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceUniSet(**kwargs)


def uts_create_from_xml(xmlConfNode):
    """
    Создание интерфейса
    :param xmlConfNode: xml-узел с настройками
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceUniSet(xmlConfNode=xmlConfNode)
