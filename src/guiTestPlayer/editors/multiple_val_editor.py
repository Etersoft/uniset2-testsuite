# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset2

from TestSuiteGlobal import *
from edit_global_functions import *
from dlg_xlist import fid as xlist_fid


class fid():
    id = 0
    node = 1
    val = 2


txtNEW = "NewItem"


class EmptyClass():
    def __init__(self):
        pass


'''
  Редкатор построен на том, что создаётся VBox (vbox_list) и
  в него добавляется (по началу 10) элементов.
  По мере необходимости, создаются новые элменеты.

  Во время работы, настройка диалога заключается в том, что
  делается hide() для неиспользуемых и show() на то количество,
  которое нужно.

  Большой минус этого подхода заключается в том, что реально виджеты
  не уничтожаются. И во время работы, пользователь может погасить,
  первых N-штук, а при этом если дальше он будет нажимать кнопку "Добавить",
  то будут создаваться новые элементы (добавляемые в конец списка),
  а не задействованы те которые "скрыты" в данный момент...
  И получатся, т.к. элементы никогда не уничтожаются, то постоянно
  при добавлении/удалении будет расти список (занимаемая память).
  Он будет "переформирован" сначала, только при редактировании следующего теста.
  Но т.к. диалог создаётся один раз и "сидит в памяти",
  то пока программа запущена, список созданных виджетов, будет равен
  самому большому "понадобившемуся" количеству при редактировании какого-либо теста.
  Т.е. если мы, например, вызвали диалог.. отредактировали 20 элементов.
  А потом вызвали этот диалог для редактирования всего 3-х элементов.
  То 20 остнутся сидеть в памяти, просто для 17-ти будет сделан hide().
  Но в действительности, вряд ли при одном редактировании, пользователю
  сможет понадобиться "очень много"... (но на всякий ввёл ограничение self.maxcount)
'''


class MultipleValEditor(gtk.HBox):
    def __init__(self, datdir, uifile="multiple_val_editor.ui"):
        gtk.HBox.__init__(self)
        self.builder = gtk.Builder()

        self.mbox_uifile = datdir + "modbus_box.ui"
        self.ubox_uifile = datdir + "uniset_box.ui"

        uifile = datdir + uifile
        self.builder.add_from_file(uifile)
        main = self.builder.get_object("main")
        main.reparent(self)

        self.builder.connect_signals(self)
        self.config = None
        self.dlg_xlist = None
        self.xmlnode = None

        self.mb_params = [
            ["e_mbreg", "mbreg", "dummy", False],
            ["e_mbaddr", "mbaddr", "mbaddr", False],
            ["e_mbfunc", "mbfunc", "mbfunc", False],
            ["e_nbit", "nbit", "nbit", False],
            ["e_vtype", "vtype", "signed", False],
            ["modbus_box", "main", "dummy", False],
            ["mb_val_box", "val_box", "dummy", False],
            ["mb_cbtn", "cbtn", "dummy", False],
            ["mb_val", "val", "val", False],
            ["mb_lbl", "lblTest", "dummy", False]
        ]
        self.mb_default_xmlnode = EmptyNode()
        self.mb_default_xmlnode.setProp("mbfunc", "4")
        self.mb_default_xmlnode.setProp("mbaddr", "1")
        self.mb_default_xmlnode.setProp("vtype", "signed")
        self.mb_default_xmlnode.setProp("nbit", "-1")
        self.mb_default_xmlnode.setProp("val", "")

        self.uniset_params = [
            ["u_id", "id", None],
            ["u_node", "node", None],
            ["u_lblTest", "lblTest", None],
            ["u_val_box", "val_box", None],
            ["u_cbtn", "cbtn", None],
            ["u_val", "val", "val", False],
            ["u_testbox", "testbox", None],
            ["uniset_box", "main", None],
            ["u_btn", "btnSel", None]
        ]

        self.uniset_ext_params = [
            ["tout", "timeout", "timeout", False],
            ["cpause", "check_pause", "check_pause", False]
        ]

        self.u_default_xmlnode = EmptyNode()
        self.u_default_xmlnode.setProp("val", "")
        self.u_default_xmlnode.setProp("id", "")

        self.maxcount = 50
        self.mb_count = 0
        self.mb_wlist = []
        self.u_count = 0
        self.u_wlist = []
        self.vbox_mb_list = self.builder.get_object("list_mb_box")
        self.vbox_u_list = self.builder.get_object("list_u_box")
        # предварительнго создаём count - полей
        for i in range(0, 10):
            self.add_mb_element()
            self.add_u_element()

        self.mb_count = len(self.mb_wlist)
        self.mb_vis_num = 0
        self.u_count = len(self.u_wlist)
        self.u_vis_num = 0

        self.scenario_type = ""

    def get_etype(self):
        return self.etype

    def add_mb_element(self):
        if len(self.mb_wlist) >= self.maxcount:
            self.builder.get_object("btnADD").set_sensitive(False)
        else:
            self.builder.get_object("btnADD").set_sensitive(True)

        b = gtk.Builder()
        # b.add_from_file(self.mbox_uifile)
        b.add_objects_from_file(self.mbox_uifile, ["main", "adjustment1", "adjustment2", "liststore2", "liststore3"])

        e = EmptyClass()
        init_builder_elements(e, self.mb_params, b)
        self.vbox_mb_list.add(e.modbus_box)
        self.mb_wlist.append([e, b])
        e.mb_val_box.show()
        e.mb_cbtn.show()
        init_elements_value(e, self.mb_params, self.mb_default_xmlnode)
        set_combobox_element(e.e_mbfunc, self.mb_default_xmlnode.prop("mbfunc"), 1)
        set_combobox_element(e.e_vtype, self.mb_default_xmlnode.prop("vtype"), 1)

    def add_u_element(self):
        if len(self.u_wlist) >= self.maxcount:
            self.builder.get_object("btnADD").set_sensitive(False)
        else:
            self.builder.get_object("btnADD").set_sensitive(True)

        b = gtk.Builder()
        b.add_objects_from_file(self.ubox_uifile, ["main", "liststore1", "liststore2", "adjustment1", "adjustment2"])
        b.connect_signals(self)

        e = EmptyClass()
        init_builder_elements(e, self.uniset_params, b)
        init_builder_elements(e, self.uniset_ext_params, b)
        self.vbox_u_list.add(e.uniset_box)
        self.u_wlist.append([e, b])
        e.u_val_box.show()
        e.u_cbtn.show()
        e.u_btn.set_data("e", e)
        init_elements_value(e, self.uniset_params, self.u_default_xmlnode)
        self.set_u_test(e, '=')
        e.tout.hide()
        e.cpause.hide()

    def set_u_test(self, e, txt):
        m = e.u_testbox.get_model()
        if m == None:
            return

        it = m.get_iter_first()
        while it is not None:
            if txt.upper() == str(m.get_value(it, 0)).upper():
                e.u_testbox.set_active_iter(it)
                return
            it = m.iter_next(it)

        e.u_testbox.set_active_iter(m.get_iter_first())

    def set_mb_count(self, num):
        if num > self.mb_count:
            # создаём дополнительные элементы
            n = num - self.mb_count
            i = 0
            while i < num:
                self.add_mb_element()
                i += 1
            self.mb_count = len(self.mb_wlist)

        # проходим по списку show сколько нужно
        # остальные hide
        i = 0
        self.mb_vis_num = 0
        for e, b in self.mb_wlist:
            if i < num:
                if e.modbus_box.get_visible() == False:
                    e.modbus_box.show()
                    init_elements_value(e, self.mb_params, self.mb_default_xmlnode)
                    select_cbox_element(e.e_mbfunc, self.mb_default_xmlnode.prop("mbfunc"), 1)
                    select_cbox_element(e.e_vtype, self.mb_default_xmlnode.prop("vtype"), 1)

                self.mb_vis_num += 1
            else:
                e.modbus_box.hide()

            i += 1

    def set_u_count(self, num):
        if num > self.u_count:
            # создаём дополнительные элементы
            n = num - self.u_count
            i = 0
            while i < num:
                self.add_u_element()
                i += 1
            self.u_count = len(self.u_wlist)

        # проходим по списку show сколько нужно
        # остальные hide
        i = 0
        self.u_vis_num = 0
        for e, b in self.u_wlist:
            if i < num:
                if e.uniset_box.get_visible() == False:
                    e.uniset_box.show()
                    init_elements_value(e, self.uniset_params, self.u_default_xmlnode)
                    if self.config:
                        create_nodes_box(e.u_node, self.config)
                    else:
                        e.u_node.get_model().clear()

                self.u_vis_num += 1
            else:
                e.uniset_box.hide()

            i += 1

    def init(self, xmlnode, config, dlg_xlist, xml):
        self.multiple_init(xmlnode, config, dlg_xlist, "check", xml)

    def multiple_init(self, xmlnode, config, dlg_xlist, xmlfield, xml):

        self.dlg_xlist = dlg_xlist
        self.xmlnode = xmlnode
        self.config = config
        # self.mb_wlist = []
        #self.u_wlist = []
        vbox_list = self.builder.get_object("list_box")

        t_node = xml.findNode(xml.getDoc(), "TestList")[0]
        self.scenario_type = to_str(t_node.prop("type"))
        if self.scenario_type == "":
            self.scenario_type = "uniset"

        if self.scenario_type == "modbus":
            self.vbox_u_list.hide()
            self.vbox_mb_list.show()
            s_id = to_str(xmlnode.prop(xmlfield))

            idlist = s_id.split(",")
            i = 0
            id_count = len(idlist)
            if id_count <= 0:
                id_count = 5

            self.set_mb_count(id_count)
            k = 0
            for i in idlist:
                v = i.split('=')
                if len(v) > 1:
                    s_id = v[0]
                    s_val = v[1]
                else:
                    s_id = i
                    s_val = ""

                mbaddr, mbreg, mbfunc, nbit, vtype = get_mbquery_param(s_id, "0x04", True)

                e, b = self.mb_wlist[k]
                e.e_mbreg.set_text(mbreg)
                e.e_mbaddr.set_value(to_int(mbaddr))
                select_cbox_element(e.e_mbfunc, mbfunc, 1)
                e.e_nbit.set_value(to_int(nbit))
                select_cbox_element(e.e_vtype, vtype, 1)
                e.mb_val.set_text(s_val)
                k += 1
        else:
            self.vbox_u_list.show()
            self.vbox_mb_list.hide()

            s_id = to_str(xmlnode.prop(xmlfield))

            idlist = s_id.split(",")
            i = 0
            id_count = len(idlist)
            if id_count <= 0:
                id_count = 5

            self.set_u_count(id_count)
            k = 0
            for i in idlist:
                v = i.split('=')
                if len(v) > 1:
                    s_id = v[0]
                    s_val = v[1]
                else:
                    s_id = i
                    s_val = ""

                s_id, s_node_full = get_sinfo(s_id)
                s_name = s_id

                e, b = self.u_wlist[k]
                create_nodes_box(e.u_node, config)

                s_node = get_node_info(s_node_full)
                if is_id(s_node):
                    select_cbox_element(e.u_node, s_node, 1)
                else:
                    select_cbox_element(e.u_node, s_node, 0)

                e.u_id.set_text(s_name)
                e.u_val.set_text(s_val)
                k += 1

    def save(self):
        return self.multiple_save("check")

    def multiple_save(self, xmlfield):

        if self.xmlnode == None:
            return False

        s_out = ""

        if self.scenario_type == "modbus":
            for e, b in self.mb_wlist:

                if e.modbus_box.get_visible() == False:
                    continue

                if e.e_mbreg.get_text() == "":
                    continue

                if e.e_mbfunc.get_active_iter() == None:
                    continue

                if e.e_vtype.get_active_iter() == None:
                    continue

                # "mbreg@mbaddr:mbfunc:nbit:vtype"
                prefix = "%s," % s_out
                if s_out == "":
                    prefix = ""

                s_out = "%s%s@%s:%s:%s:%s=%s" % (prefix,
                                                 e.e_mbreg.get_text(),
                                                 to_str(e.e_mbaddr.get_value_as_int()),
                                                 e.e_mbfunc.get_model().get_value(e.e_mbfunc.get_active_iter(), 1),
                                                 to_str(e.e_nbit.get_value_as_int()),
                                                 e.e_vtype.get_model().get_value(e.e_vtype.get_active_iter(), 1),
                                                 e.mb_val.get_text()
                )

        else:
            for e, b in self.u_wlist:

                if e.uniset_box.get_visible() == False:
                    continue

                if e.u_id.get_text() == "":
                    continue

                    # if e.u_val.get_text() == "":
                #                  e.u_val.set_text("0")

                prefix = "%s," % s_out
                if s_out == "":
                    prefix = ""

                snode = ""
                it = e.u_node.get_active_iter()
                if it:
                    snode = e.u_node.get_model().get_value(it, 0)
                    if snode != "":
                        snode = "@%s" % snode

                s_out = "%s%s%s=%s" % (prefix, e.u_id.get_text(), snode, e.u_val.get_text())

        # print "SAVE ITEM: %s"%s_out
        if s_out != "":
            self.xmlnode.setProp(xmlfield, s_out)
            self.xmlnode.setName(self.get_etype())
            return True

        return False

    def on_btnADD_clicked(self, btn):
        if self.vbox_mb_list.get_visible():
            self.set_mb_count(self.mb_vis_num + 1)
        elif self.vbox_u_list.get_visible():
            self.set_u_count(self.u_vis_num + 1)

    def on_btnDEL_clicked(self, btn):
        if self.vbox_mb_list.get_visible():
            for e, b in self.mb_wlist:
                if e.mb_cbtn.get_active():
                    e.modbus_box.hide()
                    e.mb_cbtn.set_active(False)
                    self.mb_vis_num -= 1
        elif self.vbox_u_list.get_visible():
            for e, b in self.u_wlist:
                if e.u_cbtn.get_active():
                    e.uniset_box.hide()
                    e.u_cbtn.set_active(False)
                    e.u_id.set_text("")
                    e.u_val.set_text("")
                    self.u_vis_num -= 1

    def on_btnSel_clicked(self, btn):
        e = btn.get_data("e")
        s_id = e.u_id.get_text()
        snode = None
        if is_id(s_id):
            it = self.dlg_xlist.set_selected_id(s_id, self.config)
            if it != None:
                s_name = self.dlg_xlist.model.get_value(it, xlist_fid.name)
                snode = self.dlg_xlist.model.get_value(it, xlist_fid.xmlnode)
        else:
            it = self.dlg_xlist.set_selected_name(s_id, self.config)
            if it:
                snode = self.dlg_xlist.model.get_value(it, xlist_fid.xmlnode)

        snode = self.dlg_xlist.run(self.builder.get_object("MainWindow"), snode)
        if snode == None:
            e.u_id.set_text("")
            return

        e.u_id.set_text(snode.prop("name"))
        