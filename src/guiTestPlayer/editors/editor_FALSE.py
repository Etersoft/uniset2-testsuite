# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset2

from simple_editor import *


class Editor_FALSE(SimpleEditor):
    def __init__(self, datdir):
        SimpleEditor.__init__(self, datdir)

        self.set_lbl_text("= FALSE")
        self.field = "test"
        self.field_val = "false"
        self.etype = "check"


def create_module(datdir):
    return Editor_FALSE(datdir)


def module_name():
    return "FALSE"
