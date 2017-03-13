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
#         self.level = 0  # уровень рекурсии
#         self.start_time = time.time()
#
#         for k,v in kwargs.items():
#             if hasattr(object, k):
#                 setattr(object, k, v)

def copy_dict_attrs(source_dict):
    res = dict()
    for k, v in source_dict.items():
        if not k in res:
            res[k] = v

    return res

def make_default_item():
    item = dict()
    item['name'] = ''
    item['comment'] = ''
    item['call_level'] = None
    item['result'] = t_NONE
    item['text'] = ''
    item['items'] = list()
    item['xmlnode'] = None
    item['filename'] = ''
    item['prev'] = None
    item['item_type'] = ''  # action,check,test
    item['tag'] = ''  # первый тег на котором "сработал" фильтр
    item['tags'] = ''  # теги
    item['level'] = 0  # уровень где вызывается тест (уровень рекурсии)
    item['start_time'] = time.time()
    item['test_type'] = '' # TEST, EQUAL, OUTLINK, LINK, =, !=, >, >=, <, <=, MSLEEP, SCRIPT, и т.п. (см. docs)

    # датчик на котором произошёл вылет теста (в формате name@node)
    # так же в этом поле может быть два датчика (в случае <compare> проверок)
    # поэтому перед использованием надо проверять len(item['faulty_sensor'])==2
    item['faulty_sensor'] = None
    item['ui'] = None

    return item


def make_fail_result(text, ftest_type='(TestSuiteXMLPlayer)', copyFrom=None):
    fail = make_default_item()
    if copyFrom:
        fail = copy_dict_attrs(copyFrom)
    fail['result'] = t_FAILED
    fail['text'] = text
    fail['test_type'] = ftest_type
    return fail


def make_info_item(text, ftest_type='(TestSuiteXMLPlayer)', copy_from=None):
    info = make_default_item()
    if copy_from:
        info = copy_dict_attrs(copy_from)

    info['test_type'] = ftest_type
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


def get_arg_param(param, defval=""):
    for i in range(0, len(sys.argv)):
        if sys.argv[i] == param:
            if i + 1 < len(sys.argv):
                return sys.argv[i + 1]
            else:
                break

    return defval


def get_arg_int(param, defval=0):
    for i in range(0, len(sys.argv)):
        if sys.argv[i] == param:
            if i + 1 < len(sys.argv):
                return UGlobal.to_int(sys.argv[i + 1])
            else:
                break

    return defval


def check_arg_param(param, defval=""):
    for i in range(0, len(sys.argv)):
        if sys.argv[i] == param:
            return True

    return defval


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
