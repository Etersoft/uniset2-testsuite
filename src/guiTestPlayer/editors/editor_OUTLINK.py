# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset2

from edit_global_functions import *
from dlg_xlist import xfid as xlist_fid
from TestSuiteGlobal import *


class Editor_OUTLINK(gtk.HBox):
    def __init__(self, datdir, uifile="editor_OUTLINK.ui"):

        gtk.HBox.__init__(self)
        self.builder = gtk.Builder()

        uifile = datdir + uifile
        self.builder.add_from_file(uifile)
        main = self.builder.get_object("main")
        main.reparent(self)

        self.cbox = self.builder.get_object("linkbox")
        self.model = gtk.ListStore(str, object)
        self.cbox.set_model(self.model)

        self.fname = self.builder.get_object("ent_filename")
        self.replist = self.builder.get_object("replace")

        self.builder.connect_signals(self)
        self.config = None
        self.xmlnode = None
        self.etype = "outlink"

    def get_etype(self):
        return self.etype

    def on_btnSelFile_clicked(self, btn):
        old_filename = self.fname.get_text()
        dlg = gtk.FileChooserDialog(_("File selection"), action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dlg.set_select_multiple(False)
        res = dlg.run()
        dlg.hide()
        if res == gtk.RESPONSE_OK:
            self.fname.set_text(dlg.get_filename())
            if old_filename != self.fname.get_text():
                p_node = self.xmlnode.parent
                # исключаем возможность задать ссылку на себя
                exclude = ["name", p_node.prop("name")]
                create_test_box(self.cbox, self.fname.get_text(), [], exclude)

    def init(self, xmlnode, config, dlg_xlist, xml):
        sel = []
        exclude = []
        self.xmlnode = xmlnode
        if xmlnode:
            filename = to_str(xmlnode.prop("file"))
            self.fname.set_text(filename)
            self.replist.set_text(to_str(xmlnode.prop("replace")))

            sel = get_sinfo(xmlnode.prop("link"), '=')
            p_node = xmlnode.parent
            # исключаем возможность задать ссылку на себя
            exclude = ["name", p_node.prop("name")]

        self.model.clear()
        self.model.prepend(["ALL", None])
        if xmlnode and xmlnode.prop("link") == "ALL":
            self.cbox.set_active_iter(self.model.get_iter_first())

        create_test_box(self.cbox, filename, sel, exclude)


    def save(self):

        if self.xmlnode == None:
            return False

        iter = self.cbox.get_active_iter()
        if not iter:
            return False

        # xmlnode = self.cbox.get_model().get_value(iter,1)
        linkname = self.cbox.get_model().get_value(iter, 0)
        # т.к. список строили по name, то сохраняем ссылку в виде name=XXX
        if linkname == "ALL":
            self.xmlnode.setProp("link", "ALL")
        else:
            self.xmlnode.setProp("link", "name=%s" % linkname)

        self.xmlnode.setProp("file", self.fname.get_text())
        self.xmlnode.setProp("replace", self.replist.get_text())
        self.xmlnode.setProp("test", "outlink")
        return True


def create_module(datdir):
    return Editor_OUTLINK(datdir)


def module_name():
    return "OUTLINK"
