#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uniset2.UGlobal import *
from uniset2.pyUExceptions import UException
from uniset2.pyUConnector import *
from UTestInterface import *


class UTestInterfaceUniSet(UTestInterface):
    def __init__(self, xmlfile, params):

        UTestInterface.__init__(self, 'uniset')
        self.ui = UConnector(params, xmlfile)
        self.supplierID = DefaultID
        self.ignore_nodes = False

    def set_ignore_nodes(self, state):
        self.ignore_nodes = state

    def parseID(self, name):
        return to_sid(name, self.ui)

    def validateConfiguration(self):
        #todo Реализовать функцию проверки конфигурации
        return [True, ""]

    def validateParameter(self, s_id):

        try:
            s = self.parseID(s_id)
            if s[0] == DefaultID:
                return [False, "Unknown ID for '%s'" % str(s_id)]

            return [True, ""]

        except UException, e:
            return [False, "%s" % e.getError()]

    def getValue(self, s_id):

        try:
            s = self.parseID(s_id)
            if self.ignore_nodes:
                s[1] = DefaultID

            return self.ui.getValue(s[0], s[1])

        except UException, e:
            raise TestSuiteException(e.getError())

    def setValue(self, s_id, s_value, supplierID):
        try:
            s = self.parseID(s_id)
            if self.ignore_nodes:
                s[1] = DefaultID

            self.ui.setValue(s[0], s_value, s[1], self.supplierID)
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
