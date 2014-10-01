#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import gobject

from TestSuiteInterface import *


class TestSuitePlayer(gobject.GObject):
    def __init__(self, testsuiteinterface=None):
        self.tsi = testsuiteinterface
       