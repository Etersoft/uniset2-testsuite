# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset2

from multiple_val_editor import *


class Editor_MULTICHECK(MultipleValEditor):
    def __init__(self, datdir):
        MultipleValEditor.__init__(self, datdir)
        self.field = "test"
        self.field_val = "multicheck"
        self.etype = "check"


    def init(self, xmlnode, config, dlg_xlist, xml):
        self.multiple_init(xmlnode, config, dlg_xlist, "id", xml)

    def save(self):
        return self.multiple_save("id")


def create_module(datdir):
    return Editor_MULTICHECK(datdir)


def module_name():
    return "MULTICHECK"
