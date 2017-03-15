# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset2

from TestSuiteGlobal import *


txtNEW = "NewName"


class ScenarioParamEditor():
    def __init__(self, builder):

        self.builder = builder
        self.dlg = self.builder.get_object("dlgScenarioParameters")
        btn = self.builder.get_object("clist_btnPlus")
        btn.connect('clicked', self.on_clist_btnPlus_clicked)
        btn = self.builder.get_object("clist_btnMinus")
        btn.connect('clicked', self.on_clist_btnMinus_clicked)
        btn = self.builder.get_object("rlist_btnPlus")
        btn.connect('clicked', self.on_rlist_btnPlus_clicked)
        btn = self.builder.get_object("rlist_btnMinus")
        btn.connect('clicked', self.on_rlist_btnMinus_clicked)

        self.builder.connect_signals(self)
        self.tvconf = self.builder.get_object("tvconf")
        self.cmodel = gtk.ListStore(str, str, bool, object)
        self.tvconf.set_model(self.cmodel)
        cell = self.builder.get_object("cell_alias")
        cell.connect('edited', self.col_edited_txt, self.tvconf.get_model(), 0)
        cell = self.builder.get_object("cell_config")
        cell.connect('edited', self.col_edited_txt, self.tvconf.get_model(), 1)

        self.tvrun = self.builder.get_object("tvrun")
        self.rmodel = gtk.ListStore(str, str, str, bool, bool, str, int, bool, bool, object)
        self.tvrun.set_model(self.rmodel)

        cell = self.builder.get_object("cell_script")
        cell.connect('edited', self.col_edited_txt, self.tvrun.get_model(), 0)

        cell = self.builder.get_object("cell_args")
        cell.connect('edited', self.col_edited_txt, self.tvrun.get_model(), 1)

        cell = self.builder.get_object("cell_chdir")
        cell.connect('edited', self.col_edited_txt, self.tvrun.get_model(), 2)

        cell = self.builder.get_object("cell_ign_term")
        cell.connect('toggled', self.on_cb_changed, self.tvrun.get_model(), 3)

        cell = self.builder.get_object("cell_ign_run_failed")
        cell.connect('toggled', self.on_cb_changed, self.tvrun.get_model(), 4)

        cell = self.builder.get_object("cell_name")
        cell.connect('edited', self.col_edited_txt, self.tvrun.get_model(), 5)

        cell = self.builder.get_object("cell_after_pause")
        cell.connect('edited', self.col_edited_txt, self.tvrun.get_model(), 6)

        cell = self.builder.get_object("cell_silent_mode")
        cell.connect('toggled', self.on_cb_changed, self.tvrun.get_model(), 7)

    def on_clist_btnPlus_clicked(self, btn):
        # (model, iter) = self.tvconf.get_selection().get_selected()
        #        if not iter:
        #           return False

        it = self.tvconf.get_model().append(["", "", True, None])
        self.tvconf.set_cursor(self.tvconf.get_model().get_path(it))

    def on_clist_btnMinus_clicked(self, btn):
        (model, iter) = self.tvconf.get_selection().get_selected()
        if not iter:
            return False

        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, _("Are you sure?"))
        res = dlg.run()
        dlg.hide()
        if res == gtk.RESPONSE_NO:
            return False

        xmlnode = model.get_value(iter, None)
        if xmlnode:
            xmlnode.unlinkNode()

        model.remove(iter)

    def on_rlist_btnPlus_clicked(self, btn):
        # (model, iter) = self.tvrun.get_selection().get_selected()
        #        if not iter:
        #           return False
        it = self.tvrun.get_model().append(["", "", "", False, False, txtNEW, 0, True, True, None])
        self.tvrun.set_cursor(self.tvrun.get_model().get_path(it))

    def on_rlist_btnMinus_clicked(self, btn):
        (model, iter) = self.tvrun.get_selection().get_selected()
        if not iter:
            return False

        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, _("Are you sure?"))
        res = dlg.run()
        dlg.hide()
        if res == gtk.RESPONSE_NO:
            return False

        xmlnode = model.get_value(iter, None)
        if xmlnode:
            xmlnode.unlinkNode()

        model.remove(iter)

    def on_cb_changed(self, cb, path, model, fid):
        cb.set_active(not cb.get_active())
        iter = model.get_iter(path)
        model.set_value(iter, fid, None)

    def col_edited_txt(self, cell, path, new_text, model, field):
        model[path][field] = new_text

    def run(self, tsi, player):

        xml = player.xml
        self.cmodel.clear()
        cnode = xml.findNode(xml.getDoc(), "Config")[0]
        config_node = None
        if cnode != None:
            cnode = xml.findNode(cnode, "aliases")[0]
            if cnode != None:
                config_node = cnode
                cnode = config_node.children
                while cnode != None:
                    self.cmodel.append([cnode.prop("alias"), cnode.prop("confile"), True, cnode])
                    cnode = xml.nextNode(cnode)

        self.rmodel.clear()
        rlist = xml.findNode(xml.getDoc(), "RunList")[0]
        rlist_node = rlist
        if rlist != None:
            node = xml.firstNode(rlist.children)
            # print "load RUNLIST from " + str(xml.getFileName())
            cmodel = self.tvrun.get_model()
            while node != None:
                cmodel.append([
                    to_str(node.prop("script")),
                    to_str(node.prop("args")),
                    to_str(node.prop("chdir")),
                    to_str(node.prop("ignore_terminated")),
                    to_str(node.prop("ignore_run_failed")),
                    to_str(node.prop("name")),
                    to_int(node.prop("after_run_pause")),
                    to_int(node.prop("silent_mode")),
                    True,
                    node])
                node = xml.nextNode(node)

        ret = self.dlg.run()
        self.dlg.hide()
        if ret == 100:
            # save...
            model = self.tvrun.get_model()
            rlist = rlist_node
            if rlist == None:
                rlist = xml.getDoc().newChild(None, "RunList", None)
                tnode = xml.findNode(xml.getDoc(), "TestList")[0]
                rlist = tnode.addPrevSibling(rlist)
                print "CREATE <RunList> section.."

            it = model.get_iter_first()
            while it is not None:

                if model.get_value(it, None) == "" or model.get_value(it, None) == txtNEW:
                    it = model.iter_next(it)
                    continue

                xnode = model.get_value(it, None)
                if xnode == None:
                    xnode = rlist.newChild(None, "item", None)

                xnode.setProp("script", model.get_value(it, None))
                xnode.setProp("args", model.get_value(it, None))
                xnode.setProp("chdir", model.get_value(it, None))
                xnode.setProp("ignore_terminated", bool2str(model.get_value(it, None)))
                xnode.setProp("ignore_run_failed", bool2str(model.get_value(it, None)))
                xnode.setProp("name", model.get_value(it, None))
                xnode.setProp("after_run_pause", str(model.get_value(it, None)))
                xnode.setProp("silent_mode", bool2str(model.get_value(it, None)))
                it = model.iter_next(it)

            model = self.tvconf.get_model()
            cnode = config_node
            if cnode == None:
                p = xml.firstNode(xml.getDoc()).children
                cnode = p.newChild(None, "Config", None)
                tnode = xml.findNode(xml.getDoc(), "TestList")[0]
                cnode = tnode.addPrevSibling(cnode)
                cnode = cnode.newChild(None, "aliases", None)
                print "CREATE <Config> section.."

            it = model.get_iter_first()
            while it is not None:
                if model.get_value(it, None) == "" and model.get_value(it, None) == "":
                    it = model.iter_next(it)
                    continue

                xnode = model.get_value(it, None)
                if xnode == None:
                    xnode = cnode.newChild(None, "item", None)

                xnode.setProp("alias", model.get_value(it, None))
                xnode.setProp("confile", model.get_value(it, None))
                it = model.iter_next(it)

        return ret
