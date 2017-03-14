#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uniset2.UGlobal as UGlobal
import time
import sys


class TestSuiteReporter():
    """ Базовый класс для формирователей отчётов """

    def __init__(self, **kwargs):
        self.start_time = time.time()
        self.finish_time = time.time()
        self.show_test_tree = False

        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def is_enabled(self):
        '''
        Включен ли данный Reporter
        :return: None
        '''
        return False

    def set_show_test_tree_mode(self, state):
        '''
        Установка флага для режима вывод дерева тестов
        :param state: TRUE или FALSE
        :return: None
        '''
        self.show_test_tree = state

    def print_log(self, item):
        '''
        Вывод лога
        :param item: текущий тест (см. TestSuiteGlobal::make_default_item)
        :return: None
        '''
        pass

    def print_actlog(self, act):
        '''
        Вывод лога для действий (action)
        :param act: текущее действие (см. TestSuiteGlobal::make_default_item)
        :return: None
        '''
        pass

    def make_report(self, tree_tests, check_scenario_mode=False):
        '''
        Формирование отчёта. Функция вызывается в конце тестирования
        :param tree_tests: Линейный список тестов (без учёта вложенности). Не содержит IGNORE тесты!
        :param check_scenario_mode: флаг режима проверки сценария
        :return: None
        '''
        pass

    def make_call_trace(self, call_trace, call_limit):
        '''
        Формирование call-trace
        :param call_trace: список вызовов тестов
        :param call_limit: ограничение на уровень вывода trace
        :return: None
        '''
        pass

    def start_tests(self, tm=None):
        if not tm:
            self.start_time = time.time()
        else:
            self.start_time = tm

    def finish_tests(self, tm=None):
        if not tm:
            self.finish_time = time.time()
        else:
            self.finish_time = tm

    def finish_test_event(self):
        pass

    @staticmethod
    def commandline_to_attr(object, arg_name, attr_def_prefix=''):
        '''
        Вспомогательная функция преобразования аргументов командной строки
        в атрибуты класса, если в классе уже существует атрибут совпадающий по имени с
        тем что указан в командной строке. При этом в аргументах командной строки ищутся
        параметры вида --arg-name-xxx и в класс добавляется атрибут 'xxx'.
        Все '-' в названии заменяются на '_'.
        Если в аргументах указан параметр --arg-name-xxx value, то в качестве значения атрибута класса
        выставляется 'value'.
        Если в аргументах указан только параметр --arg-name-xxx и всё, то в качестве значения выставляется 'True'.

        :param object: объект для добавления атрибутов
        :param arg_name: префикс для поиска аргументов (ищутся '--arg-name-xxxx')
        :param attr_def_prefix: префикс при поиске атрибутов в классе (т.е. в классе проверяются аттрибуты 'attr_def_prefix_xxx')
        :return: сколько найдено аргументов
        '''
        anum = 0
        arg_prefix = '--' + arg_name + '-'
        prefix_len = len(arg_prefix)
        for i in range(0, len(sys.argv)):
            if sys.argv[i].startswith(arg_prefix):
                attr_name = sys.argv[i][prefix_len:].replace('-', '_')
                attr_value = True

                if len(attr_name) == 0:
                    continue

                attr_name = attr_def_prefix + '_' + attr_name

                if (i + 1) < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                    attr_value = sys.argv[i + 1]

                if hasattr(object, attr_name):
                    setattr(object, attr_name, attr_value)
                    anum += 1

        return anum
