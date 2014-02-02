# -*- coding: utf-8 -*-
from gettext import gettext as _
import gtk
import gobject
import uniset
from edit_global_functions import *
from dlg_xlist import fid as xlist_fid

class Editor_LINK(gtk.HBox):

    def __init__(self,datdir,uifile="editor_LINK.ui"):

        gtk.HBox.__init__(self)
        self.builder = gtk.Builder()

        uifile = datdir+uifile
        self.builder.add_from_file(uifile)
        main = self.builder.get_object("main")
        main.reparent(self)

        self.cbox = self.builder.get_object("linkbox")
        self.model = gtk.ListStore(str, object)
        self.cbox.set_model(self.model)
        
        self.builder.connect_signals(self)
        self.config = None
        self.xmlnode = None
        self.field = "test"
        self.field_val = "link"
        self.etype = "check"        

    def get_etype(self):
        return self.etype

    def init( self, xmlnode, config, dlg_xlist, xml ):
        sel=[]
        exclude = []
        self.xmlnode = xmlnode
        if xmlnode:
           sel = get_sinfo(xmlnode.prop("link"),'=')
           p_node = xmlnode.parent
           # исключаем возможность задать ссылку на себя
           exclude = ["name",p_node.prop("name")]

        self.model.clear()
        create_test_box( self.cbox, xml.fname, sel, exclude )
    
    def save(self):
        if self.xmlnode == None:
           return False

        iter = self.cbox.get_active_iter()
        if not iter:
           return False

        #xmlnode = self.cbox.get_model().get_value(iter,1)
        linkname = self.cbox.get_model().get_value(iter,0)
        # т.к. список строили по name, то сохраняем ссылку в виде name=XXX
        self.xmlnode.setProp("link", "name=%s"%linkname )
        self.xmlnode.setProp(self.field, self.field_val)
        return True

def create_module(datdir):
    return Editor_LINK(datdir)

def module_name():
    return "LINK"
