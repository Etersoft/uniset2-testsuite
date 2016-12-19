#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uniset2 import *
import time

# различные глобальные вспомогательные функции
t_NONE = ''
t_FAILED = 'FAILED'
t_PASSED = 'PASSED'
t_IGNORE = 'IGNORE'
t_BREAK = 'BREAK'
t_PAUSE = 'PAUSE'
t_WARNING = 'WARNING'
t_UNKNOWN = 'UNKNOWN'

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
    item['item_type'] = '' # action,check,test
    item['tag'] = '' # первый тег на котором "сработал" фильтр
    item['tags'] = '' # теги
    item['nrecur'] = 0 # уровень рекурсии
    item['start_time'] = time.time()

    # датчик на котором произошёл вылет теста (в формате name@node)
    # так же в этом поле может быть два датчика (в случае <compare> проверок)
    # поэтому перед использованием надо проверять len(item['faulty_sensor'])==2
    item['faulty_sensor'] = None
    item['ui'] = None


    return item

def make_fail_result(text, type='(TestSuiteXMLPlayer)'):

    fail = make_default_item()
    fail['result'] = t_FAILED
    fail['text'] = text
    fail['type'] = type
    return fail

def make_info_item(text, type='(TestSuiteXMLPlayer)'):
    info = make_default_item()
    info['type'] = type
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
            key = to_str(v[0]).strip().strip('\n')
            val = to_str(v[1]).strip().strip('\n')
            slist.append([key, val])
        else:
            print '(get_replace_list:WARNING): (v:x) undefined value for ' + str(s)
            key = to_str(v[0]).strip().strip('\n')
            slist.append([key, 0])

    return slist

class TestSuiteReporter():
    ''' Базовый класс для формирователей отчётов '''
    def __init__(self):
        self.start_time = time.time()
        self.finish_time = time.time()
        self.showTestTreeMode = False

    def print_log(self, item):
        pass

    def print_actlog(self, act):
        pass

    def setShowTestTreeMode(self, set):
        self.showTestTreeMode = set

    def makeReport(self, results, checkScenarioMode=False):
        pass

    def makeCallTrace(self, results, call_limit):
        pass

    def start_tests(self, tm=None):
        if not tm:
            self.start_time = time.time()
        else:
            self.start_time = tm

    def finish_tests(self,tm=None):
        if not tm:
            self.finish_time = time.time()
        else:
            self.finish_time = tm

class TestSuiteException(Exception):
    def __init__( self, e = "", test_time = -1, item = dict() ):
        self.failed_item = item
        self.err = e
        self.ftime = test_time
        if test_time == -1:
            self.ftime = time.time()

    @property
    def getError(self):
        return self.err

    @property
    def getFinishTime(self):
        return self.ftime
