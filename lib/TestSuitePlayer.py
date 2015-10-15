#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gobject


class TestSuitePlayer(gobject.GObject):
    def __init__(self, testsuiteinterface=None, *args, **kwargs):
        super(TestSuitePlayer, self).__init__(*args, **kwargs)
        self.tsi = testsuiteinterface
