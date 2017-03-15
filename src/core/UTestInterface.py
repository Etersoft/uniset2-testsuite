#!/usr/bin/env python
# -*- coding: utf-8 -*-

from TestSuiteGlobal import *


class UTestInterface():
    """
    Базовый интерфейс для тестирования
    """

    def __init__(self, itest_type, **kwargs):
        self.itest_type = itest_type
        self.ignore_nodes = False

    def set_ignore_nodes(self, state):
        '''
        set ignore 'node' for tests (id@node)
        :param state: TRUE or FALSE
        '''
        self.ignore_nodes = state

    def get_interface_type(self):
        return self.itest_type

    def get_conf_filename(self):
        return ''

    def validate_parameter(self, name, context):
        """
        Validate test parameter (id@node)
        :param context:
        :param name: parameter from <check> or <action>
        :param context: dictionary with various parameters
        :return: [ RESULT, ERROR ]
        """
        return [False, "(validateParam): Unknown interface.."]

    def validate_configuration(self, context):
        """
        Validate configuration parameters  (check-scenario-mode)
        :param context: dictionary with various parameters
        :return: [ RESULT, ERROR ]
        """
        return [False, "(validateConfiguration): Unknown interface.."]

    def get_value(self, name, context):
        raise TestSuiteException("(getValue): Unknown interface..")

    def set_value(self, name, value, context):
        raise TestSuiteException("(setValue): Unknown interface...")
