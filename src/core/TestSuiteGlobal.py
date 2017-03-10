#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uniset2.UGlobal as UGlobal
import time
import os
import sys

# различные глобальные вспомогательные функции
t_NONE = ''
t_FAILED = 'FAILED'
t_PASSED = 'PASSED'
t_IGNORE = 'IGNORE'
t_BREAK = 'BREAK'
t_PAUSE = 'PAUSE'
t_WARNING = 'WARNING'
t_UNKNOWN = 'UNKNOWN'


# class TItem():
#     def __init__(self, **kwargs ):
#         self.name = ''
#         self.comment = ''
#         self.call_level = None
#         self.result = t_NONE
#         self.text = ''
#         self.items = []
#         self.xmlnode = None
#         self.filename = ''
#         self.prev = None
#         self.item_type = ''  # action,check,test
#         self.tag = ''  # первый тег на котором "сработал" фильтр
#         self.tags = ''  # теги
#         self.nrecur = 0  # уровень рекурсии
#         self.start_time = time.time()
#
#         for k,v in kwargs.items():
#             if k not in self.__dict__:
#                 self.__dict__[k] = v


def make_default_item():
    item = dict()
    item['name'] = ''
    item['comment'] = ''
    item['call_level'] = None
    item['result'] = t_NONE
    item['text'] = ''
    item['items'] = []
    item['xmlnode'] = None
    item['filename'] = ''
    item['prev'] = None
    item['item_type'] = ''  # action,check,test
    item['tag'] = ''  # первый тег на котором "сработал" фильтр
    item['tags'] = ''  # теги
    item['nrecur'] = 0  # уровень рекурсии
    item['start_time'] = time.time()

    # датчик на котором произошёл вылет теста (в формате name@node)
    # так же в этом поле может быть два датчика (в случае <compare> проверок)
    # поэтому перед использованием надо проверять len(item['faulty_sensor'])==2
    item['faulty_sensor'] = None
    item['ui'] = None

    return item


def make_fail_result(text, ftype='(TestSuiteXMLPlayer)', copyFrom=None):
    fail = make_default_item()
    if copyFrom:
        fail = copyFrom
    fail['result'] = t_FAILED
    fail['text'] = text
    fail['type'] = ftype
    return fail


def make_info_item(text, ftype='(TestSuiteXMLPlayer)', copy_from=None):
    info = make_default_item()
    if copy_from:
        info = copy_from

    info['type'] = ftype
    info['text'] = text
    return info


# Получение списка пар [key,val] из строки "key1:val1,key2:val2,.."
def get_replace_list(raw_str):
    if raw_str is None or raw_str == '':
        return []
    slist = []
    l = raw_str.split(',')
    for s in l:
        v = s.split(':')
        if len(v) > 1:
            key = UGlobal.to_str(v[0]).strip().strip('\n')
            val = UGlobal.to_str(v[1]).strip().strip('\n')
            slist.append([key, val])
        else:
            print '(get_replace_list:WARNING): (v:x) undefined value for ' + str(s)
            key = UGlobal.to_str(v[0]).strip().strip('\n')
            slist.append([key, 0])

    return slist


def is_executable(filename):
    """Проверка что файл можно запустить"""

    if not filename or len(filename) == 0:
        return False

    # если задан абсолютный путь, то сразу проверяем
    dname = os.path.dirname(filename)
    if dname:
        return os.path.exists(filename)

    # ищем по всем путям
    path = os.environ['PATH']
    if len(path) == 0:
        return False

    pdirs = path.split(':')

    for d in pdirs:
        if os.path.exists(d + '/' + filename):
            return True

    return False


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
        return False

    def print_log(self, item):
        pass

    def print_actlog(self, act):
        pass

    def set_show_test_tree_mode(self, state):
        self.show_test_tree = state

    def make_report(self, results, checkScenarioMode=False):
        pass

    def make_call_trace(self, results, call_limit):
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
        :param arg_prefix: префикс для поиска аргументов (ищутся '--arg-name-xxxx')
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

    def getArgParam(param, defval=""):
        for i in range(0, len(sys.argv)):
            if sys.argv[i] == param:
                if i + 1 < len(sys.argv):
                    return sys.argv[i + 1]
                else:
                    break

        return defval

    def getArgInt(param, defval=0):
        for i in range(0, len(sys.argv)):
            if sys.argv[i] == param:
                if i + 1 < len(sys.argv):
                    return to_int(sys.argv[i + 1])
                else:
                    break

        return defval

    def checkArgParam(param, defval=""):
        for i in range(0, len(sys.argv)):
            if sys.argv[i] == param:
                return True

        return defval


class TestSuiteException(Exception):
    def __init__(self, err='', test_time=-1, item=None):
        Exception.__init__(self)

        self.failed_item = item
        if not item:
            self.failed_item = dict()

        self.err = err
        self.ftime = test_time
        if test_time == -1:
            self.ftime = time.time()

    def getError(self):
        return self.err

    def getFinishTime(self):
        return self.ftime


class TestSuiteValidateError(TestSuiteException):
    def __init__(self, err=''):
        TestSuiteException.__init__(self, err)
