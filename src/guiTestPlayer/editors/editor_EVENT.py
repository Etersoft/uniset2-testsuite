# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset

from simple_val_editor import *
from TestSuiteGlobal import *


class Editor_EVENT(SimpleValEditor):
    def __init__(self, datdir):
        SimpleValEditor.__init__(self, datdir)
        self.field = "test"
        self.field_val = "event"
        self.etype = "check"
        self.set_lbl_text("=")
        self.tout.show()
        self.cpause.show()


def create_module(datdir):
    return Editor_EVENT(datdir)


def module_name():
    return "EVENT"
