#!/usr/bin/env python
# -*- coding: utf-8 -*-

from TestSuiteGlobal import *


class UTestInterface():
    """Базовый интерфейс для тестирования"""

    def __init__(self, itype, **kwargs):
        self.itype = itype
        self.ignore_nodes = False

    def set_ignore_nodes(self, state):
        """
        set ignore 'node' for tests (id@node)
        :param state: TRUE or FALSE
        """
        self.ignore_nodes = state

    def get_interface_type(self):
        return self.itype

    def get_conf_filename(self):
        return ''

    def validate_parameter(self, name):
        """
        Validate test parameter (id@node)
        :param name: parameter from <check> or <action>
        :return: [ RESULT, ERROR ]
        """
        return [False, "(validateParam): Unknown interface.."]

    def validate_configuration(self):
        """
        Validate configuration parameters  (check-scenario-mode)
        :return: [ RESULT, ERROR ]
        """
        return [False, "(validateConfiguration): Unknown interface.."]

    def get_value(self, name):
        raise TestSuiteException("(getValue): Unknown interface..")

    def set_value(self, name, value, supplier_id):
        raise TestSuiteException("(setValue): Unknown interface...")
