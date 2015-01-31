# -*- coding: utf-8 -*-
from gettext import gettext as _

import gtk
import gobject
import uniset2


def get_str_val(str_val):
    if str_val == None:
        return ""
    return str_val


class fid():
    id = 0
    name = 1
    tname = 2
    conf = 3
    xmlnode = 4
    xml = 5


class XListDialog():
    xml = None

    def __init__(self, datdir):

        self.builder = gtk.Builder()
        self.builder.add_from_file(datdir + "dlg_xlist.ui")
        self.builder.connect_signals(self)
        self.builder.connect_signals(self)

        self.dlg = self.builder.get_object("dlg_xlist")
        self.dlg.set_default_size(500, 400)
        self.fentry = self.builder.get_object("xlist_filter_entry")

        self.id_check = self.builder.get_object("xlist_id_cb")
        self.name_check = self.builder.get_object("xlist_name_cb")
        self.tname_check = self.builder.get_object("xlist_tname_cb")
        self.case_cb = self.builder.get_object("xlist_case_cb")

        self.cbox = self.builder.get_object("confbox")
        self.allConf = True

        # ID|Name|Textname|confile|xmlnode
        self.model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING,
                                   object, object)

        self.tv = gtk.TreeView()

        self.fmodel = self.model.filter_new()
        self.fmodel.set_visible_func(self.filter_func)

        #        self.tv.set_model(self.model)
        self.tv.set_model(self.fmodel)
        #        self.tv.set_search_equal_func(self.sfunc)

        self.tv.get_selection().set_mode(gtk.SELECTION_SINGLE)

        self.tv.set_rules_hint(True)
        self.tv.connect("button-press-event", self.on_button_press_event)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("ID"), renderer, text=fid.id)
        column.set_clickable(False)
        self.tv.append_column(column)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Name"), renderer, text=fid.name)
        column.set_clickable(False)
        self.tv.append_column(column)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("TextName"), renderer, text=fid.tname)
        column.set_clickable(False)
        self.tv.append_column(column)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Conffile"), renderer, text=fid.conf)
        column.set_clickable(False)
        self.tv.append_column(column)

        # expand all rows after the treeview widget has been realized
        #       self.connect('realize', lambda tv: tv.expand_all())

        #        self.build_tree("sensors")

        self.tv.show_all()

        scwin = self.builder.get_object("xlist_scwin")
        scwin.add(self.tv)

    def xlist_btnOK_clicked(self, btn):
        self.dlg.response(gtk.RESPONSE_OK)

    def xlist_btnCancel_clicked(self, btn):
        self.dlg.response(gtk.RESPONSE_CANCEL)

    def build_tree(self, confilst, section="sensors"):
        self.model.clear()
        mod = self.cbox.get_model()
        mod.clear()
        mod.append(["Все"])
        self.cbox.set_active_iter(mod.get_iter_first())
        self.allConf = True

        self.model.append([_("None"), "", "", "", None, None])
        for c in confilst:
            try:
                # print "********* open confile='%s'"%c
                xml = UniXML(c)
                self.build_one_tree(xml, section, c)
            except:
                self.model.append([_("Can`t open '%s'" % c), "", "", c, None, None])

            mod.append([c])

    def build_one_tree(self, xml, section, confname):
        node = xml.findNode(xml.getDoc(), section)[0].children
        while node != None:
            self.model.append([get_str_val(node.prop("id")), \
                               get_str_val(node.prop("name")), \
                               get_str_val(node.prop("textname")), confname, node, xml])
            node = xml.nextNode(node)

    def sfunc(self, model, column, key, iter):

        if model.get_value(iter, fid.id).find(key) != -1:
            return False
        if model.get_value(iter, fid.name).find(key) != -1:
            return False
            # if model.get_value(iter,2).find(key) != -1:
        #           return False

        return True

    def on_button_press_event(self, object, event):
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            (model, iter) = self.tv.get_selection().get_selected()
            if not iter:
                return False

            self.dlg.response(gtk.RESPONSE_OK)
        return False

    def set_selected_xmlnode(self, sel):
        ts = self.tv.get_selection()
        ts.unselect_all()
        self.fentry.set_text("")
        it = self.model.get_iter_first()
        while it is not None:
            if self.model.get_value(it, fid.xmlnode) == sel:  # check iterator
                ts.select_iter(self.fmodel.convert_child_iter_to_iter(it))
                self.tv.scroll_to_cell(self.model.get_path(it))
                return
            it = self.model.iter_next(it)

    def set_selected_name(self, sel, config=""):
        if sel == "" or sel == None:
            return
        ts = self.tv.get_selection()
        ts.unselect_all()
        self.fentry.set_text("")
        it = self.model.get_iter_first()
        while it is not None:
            if config != "" and self.model.get_value(it, fid.conf) != config:
                it = self.model.iter_next(it)
                continue

            if self.model.get_value(it, fid.name) == sel:
                ts.select_iter(self.fmodel.convert_child_iter_to_iter(it))
                self.tv.scroll_to_cell(self.model.get_path(it))
                return it

            it = self.model.iter_next(it)

        return None

    def set_selected_id(self, sel, config=""):
        ts = self.tv.get_selection()
        ts.unselect_all()
        self.fentry.set_text("")

        it = self.model.get_iter_first()
        while it is not None:

            if config != "" and self.model.get_value(it, fid.conf) != config:
                it = self.model.iter_next(it)
                continue

            if self.model.get_value(it, fid.id) == sel:
                ts.select_iter(self.fmodel.convert_child_iter_to_iter(it))
                self.tv.scroll_to_cell(self.model.get_path(it))
                return it
            it = self.model.iter_next(it)

        return None

    def set_selection_mode(self, mode):
        self.tv.get_selection().set_mode(mode)

    def foreach__sel_list(model, path, iter, plist):
        plist.append(path)

    def run(self, rootwin, xmlnode=None, sel_mode=gtk.SELECTION_SINGLE):
        # if rootwin:
        #            self.dlg.set_transient_for(rootwin)
        if xmlnode != None:
            self.set_selected_xmlnode(xmlnode)

        self.set_selection_mode(sel_mode)

        #        self.dlg.maximize()
        res = self.dlg.run()
        self.dlg.hide();

        if res == gtk.RESPONSE_OK:
            if sel_mode == gtk.SELECTION_SINGLE:
                (model, iter) = self.tv.get_selection().get_selected()
                if iter:
                    return model.get_value(iter, fid.xmlnode)

            elif sel_mode == gtk.SELECTION_MULTIPLE:
                (model, plist) = self.tv.get_selection().get_selected_rows()
                nlist = []
                for p in plist:
                    nlist.append(model.get_value(model.get_iter(p), fid.xmlnode))
                #               treeselection.selected_foreach(self.foreach_sel_list,plist)
                #               model = sel.get_treeview().get_model()
                #               return (model, pathlist)
                return nlist

        return None

    def xlist_filter_entry_changed(self, entry):
        self.fmodel.refilter()

    def xlist_cb_toggled(self, checkbtn):
        self.fmodel.refilter()
        if self.id_check.get_active() or self.name_check.get_active() or self.tname_check.get_active():
            self.fentry.set_sensitive(True)
        else:
            self.fentry.set_sensitive(False)

    def on_confbox_changed(self, cbox):
        self.allConf = True
        mod = self.cbox.get_model()
        if self.cbox.get_active_iter() != None and mod.get_value(self.cbox.get_active_iter(), 0) != mod.get_value(
                mod.get_iter_first(), 0):
            self.allConf = False

        self.fmodel.refilter()

    def find_str(self, s1, s2, case):

        if s1 == None or s2 == None:
            return False

        if case == False:
            if s1.upper().find(s2.upper()) != -1:
                return True
            return False

        if s1.find(s2) != -1:
            return True

        return False

    def filter_func(self, model, it):

        if it == None:
            return True

        if self.allConf == False:
            if model.get_value(it, fid.conf) != self.cbox.get_active_text():
                return False

        t = self.fentry.get_text()
        if t == "":
            return True

        case = self.case_cb.get_active()

        if self.id_check.get_active() and self.find_str(model.get_value(it, fid.id), t, case):
            return True

        if self.name_check.get_active() and self.find_str(model.get_value(it, fid.name), t, case):
            return True

        if self.tname_check.get_active() and self.find_str(model.get_value(it, fid.tname), t, case):
            return True

        if self.id_check.get_active() or self.name_check.get_active() or self.tname_check.get_active():
            return False

        return True
       