# -*- coding: utf-8 -*-
from gettext import gettext as _
import gtk
import gobject
import uniset
from simple_val_editor import *
from TestSuiteGlobal import *

class Editor_SET(SimpleValEditor):

    def __init__(self,datdir):
        SimpleValEditor.__init__(self,datdir,"editor_SET.ui")
        self.field = "name"
        self.field_val = "set"
        self.etype = "action"
        self.set_lbl_text("=")

        self.ext_params = [
            ["val2","val2","val2",False],
            ["rtime","reset_time","reset_time",False]
        ]
        init_builder_elements(self,self.ext_params,self.builder)

    def init( self, xmlnode, config, dlg_xlist, xml ):
        self.simple_val_editor_init(xmlnode, config, dlg_xlist, xml)
        init_elements_value(self,self.ext_params,xmlnode)

    def save(self):
        res = self.simple_val_editor_save()

        if res == True:
           save2xml_elements_value(self,self.ext_params,self.xmlnode)
           self.xmlnode.setProp(self.field, self.field_val)

        return res

def create_module(datdir):
    return Editor_SET(datdir)

def module_name():
    return "SET"
