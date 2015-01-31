# -*- coding: utf-8 -*-
from gettext import gettext as _
import re

import gtk
import gobject
import uniset2

from simple_val_editor import *


class Editor_CHECK(SimpleValEditor):
    def __init__(self, datdir):
        SimpleValEditor.__init__(self, datdir)

        self.etype = "check"
        self.tout.show()
        self.cpause.show()

    def init(self, xmlnode, config, dlg_xlist, xml):
        self.simple_val_editor_init(xmlnode, config, dlg_xlist, xml)


def create_module(datdir):
    return Editor_CHECK(datdir)


def module_name():
    return "CHECK"
