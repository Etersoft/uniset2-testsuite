# -*- coding: utf-8 -*-
from gettext import gettext as _
import gtk
import gobject
import uniset
from multiple_val_editor import *

class Editor_MULTISET(MultipleValEditor):

    def __init__(self,datdir):
        MultipleValEditor.__init__(self,datdir)
        self.etype = "action"
    
    def init(self, xmlnode, config, dlg_xlist, xml ):
        self.multiple_init(xmlnode,config,dlg_xlist,"set",xml)
  
    def save(self):
        return self.multiple_save("set")

def create_module(datdir):
    return Editor_MULTISET(datdir)

def module_name():
    return "MULTISET"
