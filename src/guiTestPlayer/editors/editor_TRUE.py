# -*- coding: utf-8 -*-
from gettext import gettext as _
import gtk
import gobject
import uniset
from simple_editor import *

class Editor_TRUE(SimpleEditor):

    def __init__(self,datdir):
        SimpleEditor.__init__(self,datdir)
        
        self.set_lbl_text("= TRUE")
        self.field = "test"
        self.field_val = "true"
        self.etype = "check"        
        
def create_module(datdir):
    return Editor_TRUE(datdir)

def module_name():
    return "TRUE"
