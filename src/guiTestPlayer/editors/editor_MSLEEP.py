# -*- coding: utf-8 -*-
from gettext import gettext as _
import gtk
import gobject
import uniset

class Editor_MSLEEP(gtk.HBox):

    def __init__(self,datdir):

        gtk.HBox.__init__(self)
        self.builder = gtk.Builder()
        self.builder.add_from_file(datdir+"editor_MSLEEP.ui")
        main = self.builder.get_object("main")
        main.reparent(self)
        self.field = "name"
        self.field_val = "msleep"
        self.etype = "action"        

    def get_etype(self):
        return self.etype

    def init( self, xmlnode, config, dlg_xlist, xml ):
        self.xmlnode = xmlnode
        if xmlnode:
           ent_val = self.builder.get_object("val")
           ent_val.set_text( xmlnode.prop("msec") )

    def save(self):
        if not self.xmlnode:
           return False

        ent_val = self.builder.get_object("val")
        self.xmlnode.setProp("msec",ent_val.get_text())
        return True
        

def create_module(datdir):
    return Editor_MSLEEP(datdir)

def module_name():
    return "MSLEEP"
