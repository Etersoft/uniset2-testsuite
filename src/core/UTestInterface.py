#!/usr/bin/env python
# -*- coding: utf-8 -*-

from TestSuiteGlobal import *


class UTestInterface():
    """Базовый интерфейс для тестирования"""

    def __init__(self, itype, **kwargs):
        self.itype = itype
        self.ignore_nodes = False

    def setIgnoreNodes(self, state):
        """
        set ignore 'node' for tests (id@node)
        :param state: TRUE or FALSE
        """
        self.ignore_nodes = state

    def getInterfaceType(self):
        return self.itype

    def getConfFileName(self):
        return ''

    def validateParameter(self, name):
        """
        Validate test parameter (id@node)
        :param name: parameter from <check> or <action>
        :return: [ RESULT, ERROR ]
        """
        return [False, "(validateParam): Unknown interface.."]

    def validateConfiguration(self):
        """
        Validate configuration parameters  (check-scenario-mode)
        :return: [ RESULT, ERROR ]
        """
        return [False, "(validateConfiguration): Unknown interface.."]

    def getValue(self, name):
        raise TestSuiteException("(getValue): Unknown interface..")

    def setValue(self, name, value, supplierID):
        raise TestSuiteException("(setValue): Unknown interface...")
