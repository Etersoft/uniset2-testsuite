# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset2

from simple_editor import *


class SimpleValEditor(SimpleEditor):
    def __init__(self, datdir, uifile="simple_editor.ui"):
        SimpleEditor.__init__(self, datdir, uifile)

        self.u_val_box.show()
        self.mb_val_box.show()
        self.tout.hide()
        self.cpause.hide()

    def init(self, xmlnode, config, dlg_xlist, xml):
        self.simple_val_editor_init(xmlnode, config, dlg_xlist, xml)

    def simple_val_editor_init(self, xmlnode, config, dlg_xlist, xml):
        self.simple_init(xmlnode, config, dlg_xlist, xml)

    def save(self):
        return self.simple_val_editor_save()

    def simple_val_editor_save(self):
        res = self.simple_save()

        if res == True:
            if self.scenario_type == "uniset":
                save2xml_elements_value(self, self.uniset_params, self.xmlnode)
            elif self.scenario_type == "modbus":
                save2xml_elements_value(self, self.mb_params, self.xmlnode)

        return res

        