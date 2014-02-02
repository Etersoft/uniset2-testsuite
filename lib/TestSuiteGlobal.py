#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from uniset import *

# различные глобальные вспомогательные функции
t_NONE=""
t_FAILED="FAILED"
t_PASSED="PASSED"
t_IGNORE="IGNORE"
t_BREAK="BREAK"
t_PAUSE="PAUSE"
t_WARNING = "WARNING"
t_UNKNOWN="UNKNOWN"

# Получение списка пар [key,val] из строки "key1=val1,key2=val2,.."
def get_replace_list(raw_str):
    
    if raw_str == None or raw_str == "":
       return []
    slist = []
    l = raw_str.split(",")
    for s in l:
        v = s.split(":")
        if len(v) > 1:
           key = to_str(v[0]).strip().strip("\n")
           val = to_str(v[1]).strip().strip("\n")
           slist.append([key,val])
        else:
           print "(get_replace_list:WARNING): (v:x) undefined value for " + str(s)
           key = to_str(v[0]).strip().strip("\n")
           slist.append([key,0])
    
    return slist

class TestSuiteException(Exception):
    
    def __init__(self,e="",test_time=-1):
        self.err = e
        self.ftime = test_time
        if test_time == -1:
           self.ftime = time.time()
    
    def getError(self):
        return self.err
    
    def getFinishTime(self):
        return self.ftime
