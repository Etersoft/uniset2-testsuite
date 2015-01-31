# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset2

from simple_val_editor import *
from TestSuiteGlobal import *


class Editor_TEST(gtk.HBox):
    def __init__(self, datdir, uifile="editor_TEST.ui"):

        gtk.HBox.__init__(self)
        self.builder = gtk.Builder()

        uifile = datdir + uifile
        self.builder.add_from_file(uifile)
        main = self.builder.get_object("main")
        main.reparent(self)

        self.builder.connect_signals(self)
        self.xmlnode = None
        self.ent_name = self.builder.get_object("ent_name")
        self.ign = self.builder.get_object("ignore_failed")
        self.ent_rep = self.builder.get_object("ent_replace")
        self.cbox = self.builder.get_object("confbox")
        self.model = gtk.ListStore(str, str)
        self.cbox.set_model(self.model)

        self.etype = "test"

    def get_etype(self):
        return self.etype

    def load_confbox(self, xml, config=""):
        self.model.clear()
        it = self.model.append(["Default", ""])
        self.cbox.set_active_iter(it)

        rnode = xml.findNode(xml.getDoc(), "TestList")[0]
        if rnode == None:
            print "(load_confbox): ??? not found <TestList>"
            return

        node = xml.findNode(xml.getDoc(), "Config")[0]
        if node == None:
            # print "(load_confbox): Not found <Config>"
            return

        node = xml.findNode(node, "aliases")[0]
        if node == None:
            print "(load_confbox): Not found <aliases>"
            return

        node = xml.firstNode(node.children)
        while node != None:
            cname = "%s (%s)" % (node.prop("confile"), node.prop("alias"))
            self.model.append([cname, node.prop("alias")])
            node = xml.nextNode(node)

        if config != "":
            select_cbox_element(self.cbox, config, 1)

    def init(self, xmlnode, config, dlg_xlist, xml):

        self.xmlnode = xmlnode

        conf = to_str(xmlnode.prop("config"))
        self.load_confbox(xml, conf)

        if xmlnode:
            self.ent_name.set_text(to_str(xmlnode.prop("name")))
            self.ent_rep.set_text(to_str(xmlnode.prop("replace")))
            if to_int(xmlnode.prop("ignore_failed")):
                self.ign.set_active(True)
            else:
                self.ign.set_active(False)
        else:
            self.ent_name.set_text("")
            self.ent_rep.set_text("")
            self.ign.set_active(False)

    def save(self):
        if self.xmlnode == None:
            return False

        self.xmlnode.setProp("name", self.ent_name.get_text())
        self.xmlnode.setProp("replace", self.ent_rep.get_text())
        ign = ""
        if self.ign.get_active():
            ign = "1"
        self.xmlnode.setProp("ignore_failed", ign)

        iter = self.cbox.get_active_iter()
        alias = self.cbox.get_model().get_value(iter, 1)
        self.xmlnode.setProp("config", alias)
        return True


def create_module(datdir):
    return Editor_TEST(datdir)


def module_name():
    return "TEST"
