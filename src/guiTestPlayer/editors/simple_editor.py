# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset2

from edit_global_functions import *
from dlg_xlist import fid as xlist_fid
from TestSuiteGlobal import *


class SimpleEditor(gtk.HBox):
    def __init__(self, datdir, uifile="simple_editor.ui"):

        gtk.HBox.__init__(self)
        self.builder = gtk.Builder()

        uifile = datdir + uifile
        self.builder.add_from_file(uifile)
        main = self.builder.get_object("main")
        main.reparent(self)

        self.builder.connect_signals(self)
        self.config = None
        self.dlg_xlist = None
        self.xmlnode = None
        self.snode = None
        self.scenario_type = ""

        self.mb_params = [
            ["e_mbreg", "mbreg", None],
            ["e_mbaddr", "mbaddr", None],
            ["e_mbfunc", "mbfunc", None],
            ["e_nbit", "nbit", None],
            ["e_vtype", "vtype", None],
            ["modbus_box", "main", None],
            ["mb_val_box", "val_box", None],
            ["mb_cbtn", "cbtn", None],
            ["mb_val", "val", "val", False],
            ["mb_lbl", "lblTest", None]
        ]
        self.mbox_uifile = datdir + "modbus_box.ui"
        self.mb_builder = gtk.Builder()
        self.mb_builder.add_objects_from_file(self.mbox_uifile,
                                              ["main", "adjustment1", "adjustment2", "liststore2", "liststore3"])
        self.mb_builder.connect_signals(self)
        init_builder_elements(self, self.mb_params, self.mb_builder)
        mbox = self.builder.get_object("modbus_box")
        mbox.add(self.modbus_box)

        self.uniset_params = [
            ["u_id", "id", None],
            ["u_node", "node", None],
            ["u_lblTest", "lblTest", None],
            ["u_val_box", "val_box", None],
            ["u_cbtn", "cbtn", None],
            ["u_val", "val", None],
            ["uniset_box", "main", None],
            ["u_testbox", "testbox", None],
        ]
        self.uniset_ext_params = [
            ["tout", "timeout", "timeout", False],
            ["cpause", "check_pause", "check_pause", False]
        ]

        self.uniset_uifile = datdir + "uniset_box.ui"
        self.u_builder = gtk.Builder()
        self.u_builder.add_objects_from_file(self.uniset_uifile,
                                             ["main", "liststore1", "liststore2", "adjustment1", "adjustment2"])
        self.u_builder.connect_signals(self)

        init_builder_elements(self, self.uniset_params, self.u_builder)
        init_builder_elements(self, self.uniset_ext_params, self.u_builder)

        ubox = self.builder.get_object("uniset_box")
        ubox.add(self.uniset_box)

        self.rcheck = re.compile(r"([\w@\ ]{1,})([!><]{0,}[=]{0,})([\d\ ]{1,})")

    def get_etype(self):
        return self.etype

    def set_lbl_text(self, txt):
        self.set_u_test(txt)
        self.mb_lbl.set_text(txt)

    def set_u_test(self, txt):
        m = self.u_testbox.get_model()
        if m == None:
            return

        it = m.get_iter_first()
        while it is not None:
            if txt.upper() == str(m.get_value(it, 0)).upper():
                self.u_testbox.set_active_iter(it)
                return
            it = m.iter_next(it)

        self.u_testbox.set_active_iter(m.get_iter_first())

    def get_u_test(self):
        it = self.u_testbox.get_active_iter()
        if it == None:
            return "="

        m = self.u_testbox.get_model()
        if m == None:
            return "="

        return str(m.get_value(it, 0))

    def init(self, xmlnode, config, dlg_xlist, xml):
        self.simple_init(xmlnode, config, dlg_xlist, xml)

    def simple_init(self, xmlnode, config, dlg_xlist, xml):
        self.config = config
        self.dlg_xlist = dlg_xlist
        self.snode = None
        self.xmlnode = xmlnode

        t_node = xml.findNode(xml.getDoc(), "TestList")[0]
        if t_node.prop("type") == "modbus":
            self.scenario_type = "modbus"
            self.modbus_box.show()
            self.uniset_box.hide()
            init_elements_value(self, self.mb_params, xmlnode)

            mbaddr, mbreg, mbfunc, nbit, vtype = get_mbquery_param(to_str(xmlnode.prop("id")), "0x04", True)

            self.e_mbreg.set_text(mbreg)
            self.e_mbaddr.set_value(to_int(mbaddr))
            select_cbox_element(self.e_mbfunc, mbfunc, 1)
            self.e_nbit.set_value(to_int(nbit))
            select_cbox_element(self.e_vtype, vtype, 1)

        else:
            self.scenario_type = "uniset"
            self.modbus_box.hide()
            self.uniset_box.show()
            init_elements_value(self, self.uniset_params, xmlnode)
            create_nodes_box(self.u_node, config)

            s_id = None
            s_val = None
            test = "??"
            tname = xmlnode.prop("test")
            if tname:
                clist = self.rcheck.findall(tname)
                if len(clist) >= 1:
                    test = clist[0][1].upper()
                    s_id = clist[0][0]
                    s_val = to_int(clist[0][2])
                    # elif len(clist) > 1:
                #                   test = 'MULTICHECK'
            else:
                test = "set"
                s_id = ""
                s_val = ""

            self.set_lbl_text(test)

            s_id, s_node_full = get_sinfo(s_id)

            s_name = s_id
            if xmlnode:
                if is_id(s_id):
                    it = self.dlg_xlist.set_selected_id(s_id, config)
                    if it != None:
                        s_name = self.dlg_xlist.model.get_value(it, xlist_fid.name)
                else:
                    self.dlg_xlist.set_selected_name(s_id, config)

                s_node = get_node_info(s_node_full)
                if is_id(s_node):
                    select_cbox_element(self.u_node, s_node, 1)
                else:
                    select_cbox_element(self.u_node, s_node, 0)
            else:
                self.u_node.set_active_iter(self.u_node.get_model().get_iter_first())

            self.u_id.set_text(s_name)
            self.u_val.set_text(to_str(s_val))
            self.set_u_test(test)

    def save(self):
        if self.xmlnode == None:
            return False
        return self.simple_save()

    def simple_save(self):
        txt = ""
        if self.scenario_type == "uniset":
            s_node = self.u_node.get_active_text()
            if s_node == "":
                txt = self.u_id.get_text()
            else:
                txt = "%s@%s" % (self.u_id.get_text(), s_node)

            op = self.get_u_test()
            val = self.u_val.get_text()
            txt = "%s%s%s" % (txt, op, val)
        else:
            if self.e_mbreg.get_text() != "" and self.e_mbfunc.get_active_iter() != None \
                    and self.e_vtype.get_active_iter() != None:
                # "mbreg@mbaddr:mbfunc:nbit:vtype"
                txt = "%s@%s:%s:%s:%s" % (
                    self.e_mbreg.get_text(),
                    to_str(self.e_mbaddr.get_value_as_int()),
                    self.e_mbfunc.get_model().get_value(self.e_mbfunc.get_active_iter(), 1),
                    to_str(self.e_nbit.get_value_as_int()),
                    self.e_vtype.get_model().get_value(self.e_vtype.get_active_iter(), 1),
                )

        if txt == "":
            return False

        self.xmlnode.setProp("test", txt)
        self.xmlnode.setName(self.get_etype())

        if self.tout.get_visible() == True:
            save2xml_elements_value(self, self.uniset_ext_params, self.xmlnode)

        return True

    def on_btnSel_clicked(self, btn):
        self.snode = self.dlg_xlist.run(self.builder.get_object("MainWindow"), self.snode)
        if self.snode == None:
            return

        self.u_id.set_text(self.snode.prop("name"))
