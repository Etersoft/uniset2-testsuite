# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset2

from simple_val_editor import *


class Editor_LESS(SimpleValEditor):
    def __init__(self, datdir):
        SimpleValEditor.__init__(self, datdir)

        self.set_lbl_text("<=")
        self.field = "test"
        self.field_val = "less"
        self.etype = "check"


def create_module(datdir):
    return Editor_LESS(datdir)


def module_name():
    return "LESS"
