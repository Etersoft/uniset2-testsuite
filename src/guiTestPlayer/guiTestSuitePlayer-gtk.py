#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gettext import gettext as _
import gettext
import sys
import os
import datetime

import gobject
import gtk

from TestSuiteXMLPlayer import *
from TestSuiteInterface import *
from GtkProcessMonitor import *
from dlg_xlist import *
from ScenarioParamEditor import *


# универсальный код для диалогов
# чтобы не делать обработку всех возможных кнопок 'OK'
# можно в glade назначать для всех 'OK'(в диалогах) заранее известный код возврата 
# (см. glade)
dlg_RESPONSE_OK = 100

t_PLAY = "START"
t_RUN = ""
t_NONE = ""


class gfid():
    pic = 0
    result = 1
    time = 2
    tname = 3
    bg = 4
    xmlnode = 5
    etype = 6
    t_time = 7
    pbar = 8
    pbar_vis = 9
    res_vis = 10
    num = 11
    xml = 12
    t_num = 13
    r_list = 14
    i_vis = 15
    i_fail = 16
    pmonitor = 17
    i_ign = 18
    link_xmlnode = 19
    maxnum = 20


class lid():
    dt = 0
    res = 1
    txt = 2
    maxnum = 3


bg_DEFAULT = 'white'
bg_FAILED = 'red'
bg_IGNORE = 'yellow'
bg_PASSED = 'green'
bg_BREAK = 'gray'
bg_PAUSE = 'gray'
bg_WARNING = 'yellow'

pic_DEFAULT = 'test_item.png'
pic_FAILED = 'test_failed.png'
pic_IGNORE = 'test_ignore.png'
pic_PASSED = 'test_passed.png'
pic_ACTION = 'test_action.png'
pic_BREAK = 'test_break.png'
pic_PAUSE = 'test_pause.png'
pic_WARNING = 'test_warning.png'


class guiTestSuitePlayer():
    def __init__(self):

        self.tsi = TestSuiteInterface()

        testfile = self.tsi.getArgParam("--testfile", "")
        conflist = self.tsi.getArgParam("--confile", "")
        # show_log = ts.checkArgParam("--show-test-log",False)
        #        show_actlog = ts.checkArgParam("--show-actions-log",False)
        #        show_result = ts.checkArgParam("--show-result-report",False)
        #        testname = ts.getArgParam("--test-name","")
        #        testname_prop = ts.getArgParam("--test-name-prop","name")

        cf = conflist.split(',')

        is_system_run_flag = sys.argv[0].startswith("./")
        self.datdir = ( "/usr/share/uniset2-testsuite/player/" if not is_system_run_flag else "./" )
        self.imgdir = self.datdir + "images/"
        self.moddir = self.datdir + "editors/"

        self.builder = gtk.Builder()
        self.builder.add_from_file(self.datdir + "player.ui")
        self.builder.connect_signals(self)

        self.editor_ui = gtk.Builder()
        self.editor_ui.add_from_file(self.datdir + "editor.ui")
        self.dlg_editor = self.editor_ui.get_object("dlg_editor")
        self.edit_iter = None
        self.editor = None
        self.load_editor_modules()
        self.editor_ui.connect_signals(self)
        self.sceditor = ScenarioParamEditor(self.editor_ui)

        self.clist_entry = self.builder.get_object("dlg_open_conflist")
        self.tfile_entry = self.builder.get_object("dlg_open_testfile")
        self.clist = cf
        self.tfile = testfile

        # временно для наладки
        #        self.clist_entry.set_text("configure.xml")
        #        self.tfile_entry.set_text("tests.xml")
        #        self.tfile = "tests_spec.xml"
        #        self.clist.append("configure.xml")

        if len(cf) < 1 or testfile == "":
            dlg = self.builder.get_object("dlg_open")
            res = dlg.run()
            dlg.hide()
            if res != dlg_RESPONSE_OK:
                raise TestSuiteException("Unknown testfile...")

        self.report_filename = ""

        # Init testsuite and create player
        self.tsi.init_testsuite(self.clist, False, False)
        self.player = TestSuiteXMLPlayer(self.tsi, self.tfile)
        self.play_iter = None
        self.play_selected_iter = None
        self.play_scenario = False
        self.play_stopped = False

        self.tmr = None
        self.test_conf = None
        self.play_timer_running = False
        self.pause_prev_pic = None
        self.pause_prev_bg = ""

        self.result_bg = dict()
        self.result_bg[t_PASSED] = bg_PASSED
        self.result_bg[t_FAILED] = bg_FAILED
        self.result_bg[t_IGNORE] = bg_IGNORE
        self.result_bg[t_BREAK] = bg_BREAK
        self.result_bg[t_PAUSE] = bg_PAUSE
        self.result_bg[t_WARNING] = bg_WARNING
        self.result_pic = dict()
        self.result_pic[t_PASSED] = pic_PASSED
        self.result_pic[t_FAILED] = pic_FAILED
        self.result_pic[t_IGNORE] = pic_IGNORE
        self.result_pic[t_BREAK] = pic_BREAK
        self.result_pic[t_PAUSE] = pic_PAUSE
        self.result_pic[t_WARNING] = pic_WARNING

        # Build test scenario tree
        scwin = self.builder.get_object("main_scwin")
        scwin.show()

        self.dlg_about = self.builder.get_object("aboutdialog")

        self.btn_play = self.builder.get_object("btn_play")
        self.btn_pause = self.builder.get_object("btn_pause")
        self.btn_stop = self.builder.get_object("btn_stop")
        self.btn_repeat = self.builder.get_object("btn_repeat")
        self.pb_runlist = self.builder.get_object("pbRunList")
        self.pb_runlist.set_property("visible", False)
        self.lbl_time = self.builder.get_object("lbl_time")
        #        self.ignore_failed = self.builder.get_object("mi_ignorefailed")
        self.mi_collapse = self.builder.get_object("mi_collapse")
        self.mi_expand = self.builder.get_object("mi_expand")
        self.test_popup = self.builder.get_object("test_popup")

        # LogView 
        self.logview_popup = self.builder.get_object("logview_popup")

        self.ignore_failed = self.builder.get_object("rb_ignore_failed")
        self.ignore_from_test = self.builder.get_object("rb_ignore_from_test")
        self.no_ignore_failed = self.builder.get_object("rb_ignore_no")
        self.no_view_actions = self.builder.get_object("mi_no_actions")
        self.no_view_check = self.builder.get_object("mi_no_check")
        self.lbl_stopinfo = self.builder.get_object("lbl_stopinfo")
        self.on_ignore_menu(self.no_ignore_failed)

        self.step_msec = self.builder.get_object("step_msec")

        self.model = gtk.TreeStore(gtk.gdk.Pixbuf,  # result pic
                                   str,  # result
                                   str,  # time
                                   str,  # test name
                                   str,  # backgorund
                                   object,  # xmlnode
                                   int,  # element type (TestSuiteXMLPlayer.tt)
                                   float,  # t_time
                                   int,  # progress bar
                                   'gboolean',  # progress visible
                                   'gboolean',  # result visible
                                   int,  # action or check number (item number)
                                   object,  # xml
                                   str,  # test number
                                   object,  # replace list
                                   'gboolean',  # actions vis
                                   'gboolean',  # ignore failed flag
                                   object,  # GtkProcessMonitor
                                   'gboolean',  # ignore test
                                   object  # link_xmlnode
        )


        #        self.modelfilter = self.model.filter_new()

        # create treeview
        self.fmodel = self.model.filter_new()
        self.fmodel.set_visible_func(self.tree_filter_func)
        self.tv = gtk.TreeView(self.model)
        self.tv.set_model(self.fmodel)
        self.tv.connect("button-press-event", self.on_button_press_event)
        #        self.tv.set_enable_tree_lines(True)
        #        self.tv.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)

        scwin.add(self.tv)
        self.tv.set_rules_hint(True)
        self.tv.set_enable_tree_lines(True)
        self.tv.columns_autosize()

        crnd = gtk.CellRendererText()
        col1 = gtk.TreeViewColumn(_("NN"), crnd, text=gfid.t_num)
        col1.set_clickable(False)
        self.tv.append_column(col1)

        ign = gtk.CellRendererToggle()
        ign.set_property("activatable", True)
        ign.connect('toggled', self.ignore_cell_toggled, self.model)
        col0 = gtk.TreeViewColumn(_("IGN"), ign, active=gfid.i_ign)
        col0.set_clickable(True)
        col0.connect("clicked", self.ignore_column_clicked)
        self.ignore_column_flag = False
        self.tv.append_column(col0)

        col = gtk.TreeViewColumn(_("Result and H:M:S .msec"))
        pbcell = gtk.CellRendererPixbuf()
        pbar = gtk.CellRendererProgress()
        tres = gtk.CellRendererText()
        ttime = gtk.CellRendererText()
        col.pack_start(pbcell, False)
        col.pack_start(tres, False)
        col.pack_start(pbar, True)
        col.pack_start(ttime, False)
        col.set_attributes(pbcell, pixbuf=gfid.pic)
        col.set_attributes(pbar, value=gfid.pbar, visible=gfid.pbar_vis)
        col.set_attributes(tres, text=gfid.result, cell_background=gfid.bg, visible=gfid.res_vis)
        col.set_attributes(ttime, text=gfid.time, visible=gfid.res_vis)
        self.tv.append_column(col)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Test"), renderer, text=gfid.tname)
        #        column.set_attributes(renderer,text=gfid.tname,cell_background=gfid.bg)
        column.set_clickable(False)
        self.tv.append_column(column)

        self.main_xml = self.player.xml
        self.build_test_scenario(self.player.xml)
        self.dlg_xlist = XListDialog(self.datdir)
        self.dlg_xlist.build_tree(self.player.tsi.get_config_list(), "sensors")

        # log treeview
        self.log_tv = self.builder.get_object("log_tv")
        sel = self.log_tv.get_selection().set_mode(gtk.SELECTION_NONE)
        self.log_model = self.builder.get_object("liststore1")
        log_col_dt = self.builder.get_object("log_tv_col_dt")
        log_col_dt.set_clickable(True)
        self.btn_save_log = self.builder.get_object("btn_save_log")
        self.btn_save_log.set_sensitive(False)
        self.log_tv.connect("button-press-event", self.on_logview_press_event)

        # run main window
        self.time_start = time.time()
        self.lbl_time.set_text("0:00:00")

        self.mwin = self.builder.get_object("MainWindow")
        #        self.mwin.maximize()
        self.mwin.show_all()

    def ignore_column_clicked(self, col):
        self.ignore_column_flag = not self.ignore_column_flag
        self.set_ignore_flag_all(self.model.get_iter_first(), self.ignore_column_flag)

    def ignore_cell_toggled(self, cell, path, model):

        # if self.play_timer_running:
        #   return

        cell.set_active(not cell.get_active())
        iter = model.get_iter(path)
        #        print "*** SET IGNORE: %s = %d"%(model.get_value(iter,gfid.tname),cell.get_active())
        #model.set_value(iter,gfid.i_ign, cell.get_active())
        # ставим текущему 
        self.set_ignore_flag(iter, cell.get_active())

        # и всем "дочерним"
        self.set_ignore_flag_all(model.iter_children(iter), cell.get_active())

    def set_ignore_flag(self, iter, set_val):

        if not iter:
            return

        self.model.set_value(iter, gfid.i_ign, set_val)
        if set_val == True:
            self.set_default_param(iter)
            self.model.set_value(iter, gfid.result, t_IGNORE)
            r_img = gtk.gdk.pixbuf_new_from_file(self.imgdir + pic_IGNORE)
            self.model.set_value(iter, gfid.bg, bg_IGNORE)
            self.model.set_value(iter, gfid.result, t_IGNORE)
            self.model.set_value(iter, gfid.pic, r_img)
            self.model.set_value(iter, gfid.res_vis, True)
            self.model.set_value(iter, gfid.pbar_vis, False)
        else:
            self.set_default_param(iter)

    def set_ignore_flag_all(self, it, set_flag):

        while it is not None:
            it1 = self.model.iter_children(it)
            while it1 is not None:
                self.set_ignore_flag(it1, set_flag)
                it2 = self.model.iter_children(it1)
                if it2 != None:
                    self.set_ignore_flag_all(it2, set_flag)
                it1 = self.model.iter_next(it1)

            self.set_ignore_flag(it, set_flag)
            it = self.model.iter_next(it)

    def on_button_press_event(self, object, event):
        (model, iter) = self.tv.get_selection().get_selected()

        if not iter:
            return False

        # если уже запущено "проигрывание", игнорируем
        if self.play_timer_running:
            return False

        if event.button == 3:
            self.test_popup.popup(None, None, None, event.button, event.time)
            t = model.get_value(iter, gfid.etype)
            # if t == tt.Test:
            #              self.builder.get_object("mi_addCheck").set_sensitive(False)
            #           else:
            #              self.builder.get_object("mi_addCheck").set_sensitive(True)

            return False

        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.on_edit(model, iter)

        return False

    def on_mi_del_activate(self, mitem):
        (model, iter) = self.tv.get_selection().get_selected()

        if not iter:
            return

        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, _("Are you sure?"))
        res = dlg.run()
        dlg.hide()
        if res == gtk.RESPONSE_NO:
            return False

        xmlnode = model.get_value(iter, gfid.xmlnode)
        if xmlnode:
            xmlnode.unlinkNode()

        c_iter = model.convert_iter_to_child_iter(iter)
        self.model.remove(c_iter)

        self.rebuild_tree(None)

    def on_mi_add_check_activate(self, mitem):
        (model, iter) = self.tv.get_selection().get_selected()

        if not iter:
            return

        t = model.get_value(iter, gfid.etype)
        xmlnode = model.get_value(iter, gfid.xmlnode)
        xml = model.get_value(iter, gfid.xml)
        if t == tt.Test:
            p_node = xmlnode
            xmlnode = xml.lastNode(p_node.children)
        else:
            p_node = xmlnode.parent

        new_xmlnode = p_node.newChild(None, "check", None)
        if xmlnode:
            new_xmlnode = xmlnode.addNextSibling(new_xmlnode)

        c_iter = model.convert_iter_to_child_iter(iter)

        it1 = c_iter
        if t == tt.Test:
            it1 = self.model.append(c_iter,
                                    [None, '', '', "New check", bg_DEFAULT, new_xmlnode, tt.Check, 0, 0, False, True, 0,
                                     xml, "", None, False, True, None, False, None])
        else:
            it1 = self.model.insert_after(None, c_iter,
                                          [None, '', '', "New check", bg_DEFAULT, new_xmlnode, tt.Check, 0, 0, False,
                                           True, 0, xml, "", None, False, True, None, False, None])

        it2 = model.convert_child_iter_to_iter(it1)
        self.on_edit(model, it2, True)

    def on_mi_add_test_activate(self, mitem):
        (model, iter) = self.tv.get_selection().get_selected()

        if not iter:
            return

        t = model.get_value(iter, gfid.etype)

        if t != tt.Test:
            iter = model.iter_parent(iter)

        xmlnode = model.get_value(iter, gfid.xmlnode)
        xml = model.get_value(iter, gfid.xml)
        p_node = xmlnode.parent
        new_xmlnode = p_node.newChild(None, "test", None)
        if xmlnode:
            new_xmlnode = xmlnode.addNextSibling(new_xmlnode)

        c_iter = model.convert_iter_to_child_iter(iter)

        it1 = self.model.insert_after(None, c_iter,
                                      [None, '', '', "New test", bg_DEFAULT, new_xmlnode, tt.Test, 0, 0, False, True, 0,
                                       xml, "", None, False, True, None, False, None])
        it2 = model.convert_child_iter_to_iter(it1)
        self.on_edit(model, it2, True)

    def on_mi_edit_activate(self, mitem):
        (model, iter) = self.tv.get_selection().get_selected()
        if not iter:
            return
        self.on_edit(model, iter)

    def on_edit(self, model, iter, newItem=False):
        tbox = self.editor_ui.get_object("testlist")
        tbox.set_sensitive(True)
        xmlnode = model.get_value(iter, gfid.xmlnode)
        old_name = xmlnode.prop("name")
        t = model.get_value(iter, gfid.etype)
        editor_name = ""
        for i in range(1, 10):
            if xmlnode.name == "test":
                editor_name = "test"
                tbox.set_sensitive(False)
                if t == tt.Link or t == tt.Outlink:
                    dlg = self.builder.get_object("dlgLinkChange")
                    res = dlg.run()
                    dlg.hide()
                    if res == 1:  # link
                        xmlnode = model.get_editor_nameue(iter, gfid.link_xmlnode)
                        tbox.set_sensitive(True)
                    elif res == 2:  # test
                        editor_name = "test"
                        break
                    else:
                        return False
            elif xmlnode.name == "action":
                tname = xmlnode.prop("set")
                if tname != None:
                    if len(tname.split(",")) > 1:
                        editor_name = "multiset"
                        break;
                    editor_name = "set"
                    break;

                tname = xmlnode.prop("msleep")
                if tname != None:
                    editor_name = "msleep"
                    break

                tname = xmlnode.prop("script")
                if tname != None:
                    editor_name = "script"
                    break
                break;

            elif xmlnode.name == "check":
                editor_name = "check"
                break;
            else:
                print "(editor): UNKNOWN item type = '%s'\n" % xmlnode.name
                return False

        self.edit_iter = iter
        # имитируем изменение в списке, чтобы нужный редактор повторно инициализировался
        # см. on_testlist_changed()
        self.set_testlist_element(editor_name)
        self.on_testlist_changed(tbox)
        res = self.dlg_editor.run()
        self.dlg_editor.hide()
        if res == 100 and self.editor != None:
            p_iter = model.convert_iter_to_child_iter(iter)
            # Сохраняем новые параметры
            res = False
            if self.editor:
                res = self.editor.save()

            if res == False:
                if newItem:
                    xmlnode.unlinkNode()
                    c_iter = model.convert_iter_to_child_iter(iter)
                    self.model.remove(c_iter)
                tbox.set_sensitive(True)
                self.edit_iter = None
                return

            if self.editor.get_etype() == "test":
                self.model.set_value(p_iter, gfid.etype, tt.Test)
            elif self.editor.get_etype() == "action":
                self.model.set_value(p_iter, gfid.etype, tt.Action)
            elif self.editor.get_etype() == "check":
                self.model.set_value(p_iter, gfid.etype, tt.Check)
                if self.editor.get_etype() == "link":
                    self.model.set_value(p_iter, gfid.etype, tt.Link)
                elif self.editor.get_etype() == "outlink":
                    self.model.set_value(p_iter, gfid.etype, tt.Link)

            p_iter = model.convert_iter_to_child_iter(iter)
            self.update_info(p_iter, old_name)
            if newItem:
                self.rebuild_tree(p_iter)
        elif newItem:
            xmlnode.unlinkNode()
            c_iter = model.convert_iter_to_child_iter(iter)
            self.model.remove(c_iter)

        tbox.set_sensitive(True)
        self.edit_iter = None


    def stop_all_processes(self, it):
        while it is not None:
            it1 = self.model.iter_children(it)
            while it1 is not None:
                self.stop_pmonitor(it1, True)
                it2 = self.model.iter_children(it1)
                if it2 != None:
                    self.stop_all_processes(it2)
                it1 = self.model.iter_next(it1)

            self.stop_pmonitor(it, True)
            it = self.model.iter_next(it)

    def on_mi_play_activate(self, mi):
        (model, iter) = self.tv.get_selection().get_selected()
        if not iter:
            return False

        p_iter = self.fmodel.convert_iter_to_child_iter(iter)
        # t = model.get_value(iter,gfid.etype)
        print "PLAY SELECTED: %s" % (self.model.get_value(p_iter, gfid.tname))

        self.play_selected_iter = p_iter
        self.on_play(p_iter)

    def on_btn_dlg_conflist_clicked(self, btn):

        dlg = gtk.FileChooserDialog(_("File selection"), action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dlg.set_select_multiple(True)
        res = dlg.run()
        dlg.hide()
        if res == gtk.RESPONSE_OK:
            self.clist = dlg.get_filenames()
            flst = ""
            for c in self.clist:
                flst += str(os.path.basename(c) + " ")
            self.clist_entry.set_text(flst.strip())

    def on_btn_dlg_testfile_clicked(self, btn):
        dlg = gtk.FileChooserDialog(_("File selection"), action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dlg.set_select_multiple(False)
        res = dlg.run()
        dlg.hide()
        if res == gtk.RESPONSE_OK:
            self.tfile = dlg.get_filename()
            self.tfile_entry.set_text(self.tfile)

    def on_MainWindow_destroy(self, destroy):
        self.play_stopped = True
        self.on_btn_stop_clicked(self.btn_stop)
        self.stop_all_processes(self.model.get_iter_first())
        gtk.main_quit()

    def on_quit_activate(self, data):
        self.play_stopped = True
        self.on_btn_stop_clicked(self.btn_stop)
        self.stop_all_processes(self.model.get_iter_first())
        gtk.main_quit()

    def get_win(self):
        return self.mwin

    def rebuild_tree(self, iter=None):

        xmlnode = None
        etype = None
        if iter:
            xmlnode = self.model.get_value(iter, gfid.xmlnode)
            etype = self.model.get_value(iter, gfid.etype)

        self.model.clear()
        self.build_test_scenario(self.player.xml)

        it = self.model.get_iter_first()
        if iter:
            it = self.find_iter(it, xmlnode, etype)
            if it:
                if etype == tt.Test:
                    self.tv.expand_row(self.model.get_path(it), True)
                else:
                    p_it = self.model.iter_parent(it)
                    self.tv.expand_row(self.model.get_path(p_it), True)

                f_it = self.fmodel.convert_child_iter_to_iter(it)
                self.tv.set_cursor(self.fmodel.get_path(f_it))

    def find_iter(self, iter, xmlnode, etype):
        while iter is not None:

            if self.model.get_value(iter, gfid.xmlnode) == xmlnode and self.model.get_value(iter, gfid.etype) == etype:
                return iter;

            it1 = self.model.iter_children(iter)
            if it1:
                res = self.find_iter(it1, xmlnode, etype)
                if res:
                    return res;

            iter = self.model.iter_next(iter)

        return None

    def build_test_scenario(self, xml, num=1, iter=None, prefix_num=""):

        # это надо сделать вначале, что бы уже работали
        # глобальные replce ..
        self.player.load_xml(xml.getFileName())
        self.player.initProcessMonitor(xml)

        node = self.player.get_begin_test_node(xml)
        node = xml.firstNode(node)
        while node != None:
            if prefix_num == "":
                s_num = "%d" % (num)
            else:
                s_num = "%s.%d" % (prefix_num, num)
            it = self.model.append(iter,
                                   [None, '', '', node.prop("name"), bg_DEFAULT, node, tt.Test, 0, 0, False, True, num,
                                    xml, s_num, None, False, True, None, False, None])
            self.set_replace_list(it, node)
            self.build_test(it, xml, node.children, num, s_num)
            num += 1
            node = xml.nextNode(node)

        return num

    def build_test(self, iter, xml, node, t_num, prefix_num):
        node = xml.firstNode(node)
        num = 1
        img = gtk.gdk.pixbuf_new_from_file(self.imgdir + pic_DEFAULT)
        while node != None:
            s_num = "%s.%d" % (prefix_num, num)
            if node.name == "check":
                test = to_str(self.player.replace(node.prop("test"))).upper()
                txt = self.tsi.get_check_info(node)
                if test == "LINK":
                    it = self.model.append(iter,
                                           [None, '', '', txt, bg_DEFAULT, node, tt.Link, 0, 0, False, True, num, xml,
                                            s_num, None, False, True, None, False, None])
                    self.build_link(it, node, xml, num, s_num)
                elif test == "OUTLINK":
                    it = self.model.append(iter,
                                           [None, '', '', txt, bg_DEFAULT, node, tt.Outlink, 0, 0, False, True, num,
                                            xml, s_num, None, False, True, None, False, None])
                    self.build_outlink(it, node, num, s_num)
                else:
                    it = self.model.append(iter,
                                           [img, '', '', txt, bg_DEFAULT, node, tt.Check, 0, 0, False, True, num, xml,
                                            s_num, None, False, True, None, False, None])
                    self.set_replace_list(it, node)
            elif node.name == "action":
                txt = self.tsi.get_action_info(node)
                it = self.model.append(iter,
                                       [img, '', '', txt, bg_DEFAULT, node, tt.Action, 0, 0, False, True, num, xml,
                                        s_num, None, False, True, None, False, None])
            else:
                print "Unknown type: '" + str(node.name) + "'. Ignore..."

            num += 1
            node = xml.nextNode(node)

        return t_num

    def build_link(self, iter, node, xml, num, s_num):
        t_name, t_field = self.player.get_link_param(node)

        r_list = self.set_replace_list(iter, node)

        # временно добавляем, что find_test работал
        # с учётом replace
        self.player.add_to_replace(r_list)

        t_node = self.player.find_test(xml, t_name, t_field)
        if t_node == None:
            print "LINK: Not found test (%s='%s')" % (t_field, t_name)
            self.model.set_value(iter, gfid.xmlnode, None)
            self.player.del_from_replace(r_list)
            return

        self.model.set_value(iter, gfid.xmlnode, t_node)
        self.model.set_value(iter, gfid.link_xmlnode, node)
        self.build_test(iter, xml, t_node.children, num, s_num)
        # удаляем, то что временно добавляли
        self.player.del_from_replace(r_list)

    def build_outlink(self, iter, node, num, s_num):

        t_file = self.player.get_outlink_filename(node)
        if t_file == "":
            print "OUTLINK: Unknown file. Use file=''"
            t_name = self.model.get_value(iter, gfid.tname)
            t_name = "%s [FAILED! Unknown file!]" % t_name
            self.model.set_value(iter, gfid.tname, t_name)
            self.model.set_value(iter, gfid.xmlnode, None)
            self.model.set_value(iter, gfid.fail, t_FAILED)
            return

        self.model.set_value(iter, gfid.link_xmlnode, node)

        r_list = self.set_replace_list(iter, node)

        # временно добавляем, что find_test работал
        # с учётом replace
        self.player.add_to_replace(r_list)

        t_xml = self.player.xmllist.get(t_file)
        if t_xml == None:
            # если в списке ещё нет, запоминаем..
            try:
                t_xml = self.player.load_xml(t_file)
            except UException, e:
                print "OUTLINK: Can`t open file='%s'." % (t_file)
                self.player.del_from_replace(r_list)
                t_name = self.model.get_value(iter, gfid.tname)
                t_name = "%s [FAILED! Can`t open file='%s']" % (t_name, t_file)
                self.model.set_value(iter, gfid.tname, t_name)
                self.model.set_value(iter, gfid.fail, t_FAILED)
                return

        # смотрим link с учтётом replace
        t_link = to_str(self.player.replace(node.prop("link")))

        if t_link == "ALL":
            self.build_test_scenario(t_xml, num, iter, s_num)
            self.player.del_from_replace(r_list)
            return

        # загружаем как обычный link (только xml - внешний)
        self.build_link(iter, node, t_xml, num, s_num)
        self.player.del_from_replace(r_list)

    def update_info(self, iter, old_name):
        t = self.model.get_value(iter, gfid.etype)
        xmlnode = self.model.get_value(iter, gfid.xmlnode)
        if t == tt.Check:
            txt = self.tsi.get_check_info(xmlnode)
            self.model.set_value(iter, gfid.tname, txt)
        elif t == tt.Action:
            txt = self.tsi.get_action_info(xmlnode)
            self.model.set_value(iter, gfid.tname, txt)
        elif t == tt.Link:
            xmlnode = self.model.get_value(iter, gfid.link_xmlnode)
            xml = self.model.get_value(iter, gfid.xml)
            num = self.model.get_value(iter, gfid.num)
            s_num = self.model.get_value(iter, gfid.t_num)
            txt = self.tsi.get_check_info(xmlnode)
            it1 = self.model.insert_after(None, iter,
                                          [None, '', '', txt, bg_DEFAULT, xmlnode, tt.Link, 0, 0, False, True, num, xml,
                                           s_num, None, False, True, None, False, None])
            self.tv.set_cursor(self.model.get_path(it1))
            self.model.remove(iter)
            self.build_link(it1, xmlnode, xml, num, s_num)
        elif t == tt.Outlink:
            xmlnode = self.model.get_value(iter, gfid.link_xmlnode)
            xml = self.model.get_value(iter, gfid.xml)
            num = self.model.get_value(iter, gfid.num)
            s_num = self.model.get_value(iter, gfid.t_num)
            txt = self.tsi.get_check_info(xmlnode)
            it1 = self.model.insert_after(None, iter,
                                          [None, '', '', txt, bg_DEFAULT, xmlnode, tt.Outlink, 0, 0, False, True, num,
                                           xml, s_num, None, False, True, None, False, None])
            self.tv.set_cursor(self.model.get_path(it1))
            self.model.remove(iter)
            self.build_outlink(it1, xmlnode, num, s_num)
        elif t == tt.Test:
            xmlnode = self.model.get_value(iter, gfid.xmlnode)
            n_name = xmlnode.prop("name")
            self.model.set_value(iter, gfid.tname, n_name)

            if n_name != old_name:
                # надо пройти по всем тестам и проверить у кого ссылка на данный тест
                it = self.model.get_iter_first()
                self.update_link(it, old_name, n_name)
        else:
            print "(update_info): update for unknown etype='%d'" % t

    def update_link(self, it, old_name, new_name):
        while it is not None:
            t = self.model.get_value(it, gfid.etype)
            if t == tt.Link or t == tt.Outlink:
                link_xmlnode = self.model.get_value(it, gfid.link_xmlnode)
                if link_xmlnode:
                    l_name, l_val = get_sinfo(link_xmlnode.prop("link"), '=')
                    if l_name == "name" and l_val == old_name:
                        l_xmlnode = self.model.get_value(it, gfid.link_xmlnode)
                        l_xmlnode.setProp("link", "name=%s" % new_name)
                        txt = self.tsi.get_check_info(l_xmlnode)
                        self.model.set_value(it, gfid.tname, txt)

            c_iter = self.model.iter_children(it)
            if c_iter != None:
                self.update_link(c_iter, old_name, new_name)

            it = self.model.iter_next(it)

    def set_replace_list(self, iter, testnode):

        r_list = []
        r = self.model.get_value(iter, gfid.r_list)
        if r != None:
            r_list = r_list + r

        r = get_replace_list(to_str(self.player.replace(testnode.prop("replace"))))
        # r = self.player.replace_list(r)
        if r != None and len(r) >= 1:
            r_list = r_list + r

        if len(r_list) >= 1:
            self.model.set_value(iter, gfid.r_list, r_list)
            return r_list

        self.model.set_value(iter, gfid.r_list, None)
        return None

    def rebuild_test_list(self, it=None):
        if it == None:
            it = self.model.get_iter_first()

        while it is not None:
            it1 = self.model.iter_children(it)
            while it1 is not None:
                if not self.model.get_value(it1, gfid.i_ign):
                    self.set_default_param(it1)
                it2 = self.model.iter_children(it1)
                if it2 != None:
                    self.rebuild_test_list(it2)
                it1 = self.model.iter_next(it1)

            if not self.model.get_value(it, gfid.i_ign):
                self.set_default_param(it)
            it = self.model.iter_next(it)

    def set_default_param(self, iter):
        img = gtk.gdk.pixbuf_new_from_file(self.imgdir + pic_DEFAULT)
        self.model.set_value(iter, gfid.result, t_NONE)
        self.model.set_value(iter, gfid.bg, bg_DEFAULT)
        self.model.set_value(iter, gfid.time, "")
        self.model.set_value(iter, gfid.t_time, 0)
        self.model.set_value(iter, gfid.pbar, 0)
        self.model.set_value(iter, gfid.i_fail, True)
        t = self.model.get_value(iter, gfid.etype)
        if t == tt.Test or t == tt.Outlink or t == tt.Link:
            self.model.set_value(iter, gfid.pic, None)
            self.model.set_value(iter, gfid.pbar_vis, False)
            self.model.set_value(iter, gfid.res_vis, False)
        elif t == tt.Check or t == tt.Action:
            self.model.set_value(iter, gfid.pic, img)
            self.model.set_value(iter, gfid.pbar_vis, False)
            self.model.set_value(iter, gfid.res_vis, True)

    def on_btn_play_clicked(self, btn):
        self.on_play(self.model.get_iter_first())

    def on_play(self, begin_iter):

        if self.play_timer_running == True:
            return

        if self.play_scenario == True:
            self.rebuild_test_list()

        self.play_iter = begin_iter

        self.play_scenario = True
        self.play_stopped = False

        self.play_timer_running = True
        self.btn_play.set_sensitive(False)
        self.btn_stop.set_sensitive(True)

        if self.start_pmonitor(self.play_iter) == False:
            self.stop_pmonitor(self.play_iter, True)
            print "*** FAILED RUN LIST for (%s) '%s'" % (self.model.get_value(self.play_iter, gfid.xml).getFileName(),
                                                         self.model.get_value(self.play_iter, gfid.tname))
            self.play_scenario = False
            return

        self.tmr = gobject.timeout_add(self.step_msec.get_value_as_int(), self.next_step_timer)
        self.btn_pause.set_sensitive(True)
        self.step_msec.set_sensitive(False)

        self.time_start = time.time()
        self.lbl_time.set_text("0:00:00")
        self.to_log(t_PLAY, "Начало тестирования. Сценарий: '%s'" % (self.tfile))

    def update_time(self):
        ttime = time.time() - self.time_start
        td = datetime.timedelta(0, ttime)
        ts = str(td).split('.')[0]
        self.lbl_time.set_text(ts)

    def next_step_timer(self):

        self.update_time()

        if not self.play_iter:
            self.on_finish_scenario()
            return False

        t = self.model.get_value(self.play_iter, gfid.etype)
        if t == tt.Test or t == tt.Outlink or t == tt.Link:
            res = self.on_begin_test(self.play_iter)
            if res == t_FAILED:
                if self.ignore_from_test.get_active() and self.model.get_value(self.play_iter, gfid.i_fail) == False:
                    self.on_finish_test(self.play_iter)
                    self.on_finish_scenario()
                    return False

                self.show_test_result(self.play_iter, res, 0)
                self.on_finish_test(self.play_iter)

                n_iter = self.model.iter_next(self.play_iter)
                if n_iter:
                    self.play_iter = n_iter
                    return True

                self.play_iter = self.model.iter_parent(self.play_iter)
                return self.unwinding_tests(self.play_iter, True)

            if res == t_IGNORE:
                self.show_test_result(self.play_iter, res, 0)
                self.on_finish_test(self.play_iter)
                if self.is_iter_equal(self.play_selected_iter, self.play_iter):
                    self.play_selected_iter = None
                    self.stop_pmonitor(self.play_iter, True)
                    self.on_finish_scenario()
                    return False

                n_iter = self.model.iter_next(self.play_iter)
                if n_iter:
                    self.play_iter = n_iter
                    return True

                return self.unwinding_tests(self.play_iter, True)

        elif t == tt.Check or t == tt.Action:
            res = self.on_play_item(self.play_iter)
            if res == t_FAILED:
                if self.no_ignore_failed.get_active() == True:
                    self.unwinding_tests(self.play_iter, False)
                    return False
                p_iter = self.model.iter_parent(self.play_iter)
                if p_iter and self.ignore_from_test.get_active() and self.model.get_value(p_iter, gfid.i_fail) == False:
                    self.unwinding_tests(self.play_iter, False)
                    # self.on_finish_test(self.play_iter)
                    #                 self.on_finish_scenario()
                    return False

        child_iter = self.model.iter_children(self.play_iter)
        if child_iter:  # outlink
            self.play_iter = child_iter
            return True

        next_iter = self.model.iter_next(self.play_iter)
        if next_iter:
            self.on_finish_test(self.play_iter)
            if self.is_iter_equal(self.play_selected_iter, self.play_iter):
                self.play_selected_iter = None
                self.stop_pmonitor(self.play_iter, True)
                self.on_finish_scenario()
                return False

            self.play_iter = next_iter
            return True

        return self.unwinding_tests(self.play_iter, True)

    def unwinding_tests(self, iter, unw_all=True):
        # Сворачиваем тесты
        f_iter = iter
        while True:
            p_iter = self.model.iter_parent(f_iter)
            if not p_iter:
                #self.on_finish_test(f_iter)
                break

            if unw_all == True:
                while True:
                    next_iter = self.model.iter_next(p_iter)
                    if not next_iter:
                        break

                    self.on_finish_test(p_iter)
                    if self.is_iter_equal(self.play_selected_iter, p_iter):
                        self.play_selected_iter = None
                        self.stop_pmonitor(p_iter, True)
                        self.on_finish_scenario()
                        return False

                    self.play_iter = next_iter
                    return True

            self.on_finish_test(p_iter)
            f_iter = p_iter
            if self.is_iter_equal(self.play_selected_iter, p_iter):
                self.play_selected_iter = None
                self.stop_pmonitor(p_iter, True)
                break

        self.on_finish_scenario()
        return False

    def is_iter_equal(self, l_iter, r_iter):

        if not l_iter or not r_iter:
            return False

        return ( self.model.get_string_from_iter(l_iter) == self.model.get_string_from_iter(r_iter) )

    def show_progress(self, iter):
        # t = self.model.get_value(iter,gfid.etype)
        #if t == tt.Test or t == tt.Outlink or t == tt.Link:
        #   return
        t_it = self.model.iter_parent(iter)
        if not t_it:
            return

        allnum = self.model.iter_n_children(t_it)
        curnum = self.model.get_value(iter, gfid.num)

        # проверяем если тест ещё не закончен, он не должен
        # участвовать в расчёте
        t_res = self.model.get_value(iter, gfid.result)
        if t_res == t_NONE:
            curnum -= 1

        self.model.set_value(t_it, gfid.pbar, ((curnum * 1.0 / allnum) * 100.0))

        # Обновляем рекурсивно по всему дереву наверх...
        #self.show_progress(t_it)

    def pmonitor_terminated(self, err):
        # print "**************** pmonitor_terminate: %s"%err
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, err)
        res = dlg.run()
        dlg.hide()
        self.on_btn_stop_clicked(self.btn_stop)

    def pmonitor_runprogress(self, run_proc, text):
        # print "**************** pmonitor_runprogress: %f"%run_proc
        self.pb_runlist.set_fraction(run_proc)
        self.pb_runlist.set_text(text)

    def on_begin_test(self, iter):
        print "begin test: " + str(self.model.get_value(iter, gfid.t_num))
        self.to_log(t_RUN, "%s. %s" % (self.model.get_value(iter, gfid.t_num), (self.model.get_value(iter, gfid.tname))))
        t = self.model.get_value(iter, gfid.etype)
        if t != tt.Test and t != tt.Outlink and t != tt.Link:
            return t_FAILED

        testnode = self.model.get_value(iter, gfid.xmlnode)

        t_ignore = to_int(self.player.replace(testnode.prop("ignore")))
        if t_ignore:
            return t_IGNORE

        t_ignore = self.model.get_value(iter, gfid.i_ign)
        if t_ignore:
            return t_IGNORE

        # log off
        self.tsi.set_logfile("", False)

        # set replace_list
        r_list = self.model.get_value(iter, gfid.r_list)
        self.player.add_to_test_replace(r_list)

        # setup player config
        self.player.test_conf = self.player.replace(testnode.prop("config"))

        ignore_failed = True
        if self.ignore_from_test.get_active():
            ignore_failed = to_int(self.player.replace(testnode.prop("ignore_failed")))
        elif self.ignore_failed.get_active() == True:
            ignore_failed = True
        elif self.no_ignore_failed.get_active() == True:
            ignore_failed = False

        self.tsi.set_ignorefailed(ignore_failed)
        self.model.set_value(iter, gfid.i_fail, ignore_failed)

        self.test_conf = self.player.replace(testnode.prop("config"))

        img = gtk.gdk.pixbuf_new_from_file(self.imgdir + pic_ACTION)

        if t == tt.Outlink or t == tt.Link:
            # runlist только для outlink-ов
            if t == tt.Outlink:
                ignore_runlist = to_int(self.player.replace(testnode.prop("ignore_runlist")))
                # Старт runlsit (только для Outlink)
                # при этом надо брать child-итератор
                # т.к. в нём хранится нужный xml...
                if ignore_runlist == False:
                    c_iter = self.model.iter_children(iter)
                    if self.start_pmonitor(c_iter) == False:
                        self.stop_pmonitor(c_iter)
                        return t_FAILED

        self.model.set_value(iter, gfid.pic, img)
        self.model.set_value(iter, gfid.pbar_vis, True)
        self.model.set_value(iter, gfid.res_vis, False)
        self.model.set_value(iter, gfid.pbar, 0)

        path = self.model.get_path(iter)
        if self.mi_expand.get_active():
            self.tv.expand_row(path, False)
        self.tv.set_cursor(path)
        return t_PASSED

    def on_finish_test(self, iter):
        t = self.model.get_value(iter, gfid.etype)
        if t != tt.Test and t != tt.Outlink and t != tt.Link:
            return

        r_list = self.model.get_value(iter, gfid.r_list)
        self.player.del_from_test_replace(r_list)

        self.stop_pmonitor(iter)

        self.player.test_conf = ""
        path = self.model.get_path(iter)
        if self.mi_collapse.get_active():
            self.tv.collapse_row(path)

        res = self.collapse_test_result(iter)
        self.show_test_result(iter, res[0], res[1])
        self.model.set_value(iter, gfid.pbar_vis, False)
        self.model.set_value(iter, gfid.res_vis, True)
        self.model.set_value(iter, gfid.result, res[0])
        self.show_progress(iter)
        print "finish test '%s' res=%s" % (str(self.model.get_value(iter, gfid.t_num)), res[0])
        self.to_log(res[0], "Завершили тест %s. %s" % (
        self.model.get_value(iter, gfid.t_num), (self.model.get_value(iter, gfid.tname))))

    def collapse_test_result(self, iter):
        ''' Успешным считается только все OK
            FAILED - только всё failed
            остальное WARNING
            Т.к. каждый тест заканчивается "свёрткой", то
            достаточно только проверить свои дочерние элементы, 
            идти в глубину не надо, т.к. когда они выполнились они
            были тоже свёрнуты..
        '''
        t_res = self.model.get_value(iter, gfid.result)
        if t_res == t_IGNORE:
            return [t_IGNORE, 0]

        res = ""
        f_res = 0  # failed count
        i_res = 0  # ignore count
        p_res = 0  # passed count
        b_res = 0  # break count
        u_res = 0  # unknown count
        w_res = 0  # warning count

        t_time = 0
        it = self.model.iter_children(iter)
        if not it:
            t_time = self.model.get_value(iter, gfid.t_time)
            res = self.model.get_value(iter, gfid.result)
            return [res, t_time]

        while it is not None:
            t_time += self.model.get_value(it, gfid.t_time)
            r = self.model.get_value(it, gfid.result)
            if r == t_FAILED:
                f_res += 1
            elif r == t_IGNORE:
                i_res += 1
            elif r == t_PASSED:
                p_res += 1
            elif r == t_BREAK:
                b_res += 1
            elif r == t_WARNING:
                w_res += 1
            else:
                u_res += 1

            # print "***test child '%s' RES=%s (f=%d w=%d p=%d b=%d i=%d)"%(self.model.get_value(it,gfid.t_num),r,f_res,w_res,p_res,b_res,i_res)
            it = self.model.iter_next(it)

        if w_res > 0:
            res = t_WARNING
        elif f_res > 0 and i_res == 0 and p_res == 0 and b_res == 0:
            res = t_FAILED
        elif i_res > 0 and p_res == 0 and f_res == 0 and b_res == 0:
            res = t_IGNORE
        elif p_res > 0 and f_res == 0 and b_res == 0:  # т.е. если есть IGNORE и PASSED, то PASED
            res = t_PASSED
        elif b_res > 0 and i_res == 0 and f_res == 0 and p_res == 0:
            res = t_BREAK
        else:
            res = t_WARNING

        # print "***collapse test '%s' RES=%s (f=%d w=%d p=%d b=%d i=%d)"%(self.model.get_value(iter,gfid.t_num),res,f_res,w_res,p_res,b_res,i_res)
        return [res, t_time]

    def show_test_result(self, iter, result, ttime):
        self.model.set_value(iter, gfid.result, result)
        self.model.set_value(iter, gfid.bg, self.result_bg[result])
        img = gtk.gdk.pixbuf_new_from_file(self.imgdir + self.result_pic[result])
        self.model.set_value(iter, gfid.pic, img)
        td = datetime.timedelta(0, ttime)
        self.model.set_value(iter, gfid.time, str(td))

    # self.tv.columns_autosize()

    def on_finish_scenario(self):
        print "finish scenario..."
        self.play_timer_running = False
        self.play_iter = self.model.get_iter_first()
        self.btn_play.set_sensitive(True)
        self.btn_pause.set_sensitive(False)
        self.btn_stop.set_sensitive(False)
        self.step_msec.set_sensitive(True)
        if self.tmr:
            gobject.source_remove(self.tmr)
        # Перед repeat надо остановить все процессы
        # чтобы повторный цикл, был корректным
        # (с точки зрения инициализации)
        # Потом можно будет вывести в настройки..
        self.stop_pmonitor(self.play_iter, True)
        if self.btn_repeat.get_active() == True:
            self.on_btn_play_clicked(self.btn_play)

    def start_pmonitor(self, iter):
        # запуск RunList
        xml = self.model.get_value(iter, gfid.xml)
        # берём встроенный монитор, но используем от него только список
        # т.к. в gtk многопоточноть плохо походит
        # используем свой GtkProcessMonitor
        pmon = self.player.get_pmonitor(xml)

        print "********* START RUNLIST (runlist=%d for %s)" % (len(pmon.plist), xml.getFileName())
        #self.model.get_value(iter,gfid.tname)
        try:
            if pmon and len(pmon.plist) > 0:
                t_mp = GtkProcessMonitor()
                pmonitor = copy.deepcopy(t_mp)
                pmonitor.init(pmon.plist, pmon.check_msec, pmon.after_run_pause * 1000)
                self.model.set_value(iter, gfid.pmonitor, pmonitor)
                pmonitor.setTerminateCallback(self.pmonitor_terminated)
                pmonitor.setRunProgressCallback(self.pmonitor_runprogress)
                self.pb_runlist.set_property("visible", True)
                ret = pmonitor.m_start(self.play_stopped)
                self.pb_runlist.set_property("visible", False)
                if ret == False:
                    return False

                if pmon.after_run_pause <= 0:
                    return True

                return self.async_wait_msec(pmonitor.after_run_pause)

            self.pb_runlist.set_property("visible", False)
            self.model.set_value(iter, gfid.pmonitor, None)
            return True

        except TestSuiteException, e:
            self.model.set_value(iter, gfid.pmonitor, None)
            return False

        self.model.set_value(iter, gfid.pmonitor, None)
        return False

    def stop_pmonitor(self, iter, stop_main=False):
        pmon = self.model.get_value(iter, gfid.pmonitor)
        if not pmon:
            return

        xml = self.model.get_value(iter, gfid.xml)

        if xml == self.main_xml and stop_main == False:
            return

        print "********* STOP RUNLIST (runlist=%d for %s)" % (len(pmon.plist), xml.getFileName())
        pmon.m_finish()
        self.model.set_value(iter, gfid.pmonitor, None)

    def on_play_item(self, iter):

        res = t_FAILED
        p = self.model.get_path(iter)
        self.tv.set_cursor(p)
        self.model.set_value(iter, gfid.result, t_NONE)

        tm_start = time.time()
        tm_finish = tm_start;

        xml = self.model.get_value(iter, gfid.xml)
        try:
            t_ignore = self.model.get_value(iter, gfid.i_ign)
            if t_ignore:
                res = t_IGNORE
            else:
                t = self.model.get_value(iter, gfid.etype)
                if t == tt.Check or t == tt.Action:
                    xmlnode = self.model.get_value(iter, gfid.xmlnode)

                    res = self.special_item(xmlnode, xml, iter)
                    if res == t_NONE:
                        res = self.player.play_item(xmlnode, xml)

        except TestSuiteException, ex:
            tm_finish = time.time()  # e.getFinishTime()
            print "(play_item): " + ex.getError()
            res = t_FAILED
        except UException, ex:
            tm_finish = time.time()
            print "(play_item): " + ex.getError()
            res = t_FAILED
        else:
            tm_finish = time.time()

        finally:
            print "***on_play_item: '%s' res=%s" % (self.model.get_value(iter, gfid.t_num), str(res))
            self.to_log(res,
                        "%s. '%s'" % (self.model.get_value(iter, gfid.t_num), (self.model.get_value(iter, gfid.tname))))
            ttime = tm_finish - tm_start
            self.model.set_value(iter, gfid.t_time, ttime)
            td = datetime.timedelta(0, ttime)
            self.model.set_value(iter, gfid.time, str(td))
            if res == t_PASSED:
                r_img = gtk.gdk.pixbuf_new_from_file(self.imgdir + pic_PASSED)
                self.model.set_value(iter, gfid.bg, bg_PASSED)
                self.model.set_value(iter, gfid.result, t_PASSED)
                self.model.set_value(iter, gfid.pic, r_img)
            elif res == t_FAILED:
                r_img = gtk.gdk.pixbuf_new_from_file(self.imgdir + pic_FAILED)
                self.model.set_value(iter, gfid.bg, bg_FAILED)
                self.model.set_value(iter, gfid.result, t_FAILED)
                self.model.set_value(iter, gfid.pic, r_img)
            elif res == t_IGNORE:
                r_img = gtk.gdk.pixbuf_new_from_file(self.imgdir + pic_IGNORE)
                self.model.set_value(iter, gfid.bg, bg_IGNORE)
                self.model.set_value(iter, gfid.result, t_IGNORE)
                self.model.set_value(iter, gfid.pic, r_img)
            elif res == t_BREAK:
                r_img = gtk.gdk.pixbuf_new_from_file(self.imgdir + pic_BREAK)
                self.model.set_value(iter, gfid.bg, bg_BREAK)
                self.model.set_value(iter, gfid.result, t_BREAK)
                self.model.set_value(iter, gfid.pic, r_img)

            # прогрессбар пересчитывать последним (!)
            # потому-что там требуется чтобы gfid.result
            # был выставлен
            self.show_progress(iter)

        return res

    def special_item(self, xmlnode, xml, iter):

        if xmlnode.name == "action" and xmlnode.prop("name") == "msleep":
            msec = to_int(xmlnode.prop("msec"))
            sec = ( msec / 1000. )
            t_end = time.time() + sec
            t_proc = 0
            txt = "waiting %d msec" % msec
            self.pb_runlist.set_property("visible", True)
            while time.time() < t_end:

                self.pmonitor_runprogress(fcalibrate(t_proc, 0.0, sec, 0.0, 1.0), txt)
                p_res = self.special_main_pending(iter)
                if p_res[0] == t_BREAK:
                    self.pb_runlist.set_property("visible", False)
                    return t_BREAK

                if p_res[0] == t_PAUSE:
                    t_end = t_end + p_res[1]

                # небольшой sleep всё-равно должен быть
                # чтобы процессор "отдыхал"
                time.sleep(0.15)
                t_proc += 0.15

            self.pb_runlist.set_property("visible", False)
            return t_PASSED

        # Т.к. в текущей версии xmlplayer ВСЕ виды тестов имеют timeout
        # то "ожижание" в тестах кроме LINK и OUTLINK мы должны реализовать сами
        if xmlnode.name == "check":
            tname = xmlnode.prop("test").upper()
            if tname == "LINK" or tname == "OUTLINK":
                return t_NONE

            t_out = to_int(xmlnode.prop("timeout"))
            # если timeout не задан, то можно вызвать стандартный play..
            if t_out == 0:
                return t_NONE

            t_sleep = to_int(xmlnode.prop("check_pause")) / 1000.

            t_sec = t_out / 1000.
            t_now = time.time()
            t_end = t_now + t_sec

            # если исходно не задано время ожидания
            # то делаем так, чтобы while сработал хотя бы раз
            if t_out == 0:
                t_end = t_now + 0.001

            t_check = t_now + t_sleep
            t_proc = 0
            txt = "wait event %d msec" % t_out
            self.pb_runlist.set_property("visible", True)

            # чтобы приложение оставалось интерактивным
            # на время ожидания, реализуем логику проверки "сами"
            #(не использую логику зашитую в self.player)
            # для этого подменяем timeout
            xmlnode.setProp("timeout", "0")

            # а так же включаем игнорирование "неудачи", т.е. сами обрабатываем..
            old_ignorefailed = self.player.tsi.get_ignorefailed()
            self.player.tsi.set_ignorefailed(True)

            while t_now < t_end:

                # проверять нужно не каждый цикл
                # а c заданным шагом
                if t_now >= t_check:
                    self.update_time()
                    t_check = t_now + t_sleep
                    res = self.player.play_item(xmlnode, xml)
                    if res == t_PASSED:
                        # возвращаем обратно
                        xmlnode.setProp("timeout", str(t_out))
                        self.player.tsi.set_ignorefailed(old_ignorefailed)
                        self.pb_runlist.set_property("visible", False)
                        return t_PASSED

                p_res = self.special_main_pending(iter)
                if p_res[0] == t_BREAK:
                    xmlnode.setProp("timeout", str(t_out))
                    self.player.tsi.set_ignorefailed(old_ignorefailed)
                    self.pb_runlist.set_property("visible", False)
                    return t_BREAK

                # увеличиваем время на время паузы
                if p_res[0] == t_PAUSE:
                    t_end = t_end + p_res[1]
                    t_check = t_check + p_res[1]

                self.pmonitor_runprogress(fcalibrate(t_proc, 0.0, t_sec, 0.0, 1.0), txt)
                # небольшой sleep всё-равно должен быть
                # чтобы процессор "отдыхал"
                time.sleep(0.15)
                t_now = time.time()
                t_proc += 0.15

            xmlnode.setProp("timeout", str(t_out))
            self.player.tsi.set_ignorefailed(old_ignorefailed)
            self.pb_runlist.set_property("visible", False)
            return t_FAILED

        return t_NONE

    def special_main_pending(self, iter):

        while gtk.events_pending():
            gtk.main_iteration()

        if self.play_stopped:
            return [t_BREAK, 0]

        self.update_time()

        if self.btn_pause.get_active():
            t_start = time.time()
            while self.btn_pause.get_active():
                # если нажата "Пауза" - ждём..
                # но проверяем нажатие "Стоп"
                while gtk.events_pending():
                    gtk.main_iteration()

                if self.play_stopped:
                    return [t_BREAK, 0]

                time.sleep(0.3)

            return [t_PAUSE, time.time() - t_start]

        return [t_NONE, 0]

    def async_wait_msec(self, msec):

        if msec <= 0:
            return

        print "*** async_wait %d msec ***" % msec
        sec = msec / 1000.
        t_now = time.time()
        t_end = t_now + sec
        t_proc = 0
        self.pb_runlist.set_property("visible", True)
        txt = "waiting %d msec" % msec
        while t_now < t_end:

            if self.play_stopped == True:
                print "***(0) BREAK async_wait ***"
                self.pb_runlist.set_property("visible", False)
                return False

            self.pmonitor_runprogress(fcalibrate(t_proc, 0.0, sec, 0.0, 1.0), txt)

            while gtk.events_pending():
                gtk.main_iteration()

            self.update_time()

            if self.play_stopped == True:
                print "***(2) BREAK async_wait ***"
                self.pb_runlist.set_property("visible", False)
                return False

            # небольшой sleep всё-равно должен быть
            # чтобы процессор "отдыхал"
            time.sleep(0.15)
            t_now = time.time()
            t_proc += 0.15

        self.pb_runlist.set_property("visible", False)
        return True

    def on_btn_stop_clicked(self, btn):

        self.play_stopped = True
        if self.play_timer_running == False:
            return

        self.to_log(t_BREAK, "Нажата кнопка 'Остановить'")
        if self.tmr:
            gobject.source_remove(self.tmr)
        t = self.model.get_value(self.play_iter, gfid.etype)
        iter = self.play_iter
        if t != tt.Test and t != tt.Outlink and t != tt.Link:
            iter = self.model.iter_parent(self.play_iter)

        self.play_stopped = True
        self.btn_repeat.set_active(False)
        self.model.set_value(iter, gfid.result, t_BREAK)
        self.model.set_value(self.play_iter, gfid.result, t_BREAK)
        self.on_finish_test(iter)
        self.on_finish_scenario()
        self.btn_pause.set_active(False)

    def on_btn_pause_toggled(self, btn):

        if self.play_timer_running == False:
            return

        #t = self.model.get_value(self.play_iter,gfid.etype)
        iter = self.play_iter
        #if t != tt.Test and t != tt.Action and t != tt.Link:
        #   iter = self.model.iter_parent(self.play_iter)

        if btn.get_active() == True:
            if self.tmr:
                gobject.source_remove(self.tmr)
            self.to_log(t_PAUSE, "Нажата кнопка 'Приостановить'")
            self.pause_prev_pic = self.model.get_value(iter, gfid.pic)
            self.pause_prev_bg = self.model.get_value(iter, gfid.bg)
            self.model.set_value(iter, gfid.result, t_PAUSE)
            self.model.set_value(iter, gfid.bg, bg_PAUSE)
            r_img = gtk.gdk.pixbuf_new_from_file(self.imgdir + pic_PAUSE)
            self.model.set_value(iter, gfid.pic, r_img)
        else:
            self.to_log(t_PAUSE, "Отжата кнопка 'Приостановить'")
            self.model.set_value(iter, gfid.result, "...")
            self.model.set_value(iter, gfid.pic, self.pause_prev_pic)
            self.model.set_value(iter, gfid.bg, self.pause_prev_bg)
            self.pause_prev_pic = None
            self.btn_play.set_sensitive(False)
            self.tmr = gobject.timeout_add(self.step_msec.get_value_as_int(), self.next_step_timer)

    def on_mi_no_actions_toggled(self, mi):
        self.fmodel.refilter()

    def on_mi_no_check_toggled(self, mi):
        self.fmodel.refilter()

    def tree_filter_func(self, model, it):

        if it == None:
            return True

        t = model.get_value(it, gfid.etype)

        if self.no_view_actions.get_active() == True and t == tt.Action:
            return False

        if self.no_view_check.get_active() == True and t == tt.Check:
            return False

        return True

    def on_ignore_menu(self, rbutton):
        if self.ignore_failed.get_active():
            self.lbl_stopinfo.set_text("игнорировать 'неудачи'")
        elif self.ignore_from_test.get_active():
            self.lbl_stopinfo.set_text("в соответсвии с тестом")
        elif self.no_ignore_failed.get_active():
            self.lbl_stopinfo.set_text("при первой 'неудаче'")
        else:
            self.lbl_stopinfo.set_text("...")

    def to_log(self, res, txt):
        dt = datetime.datetime.today()
        #        self.log_model.prepend([dt.strftime("%Y-%m-%d %H:%M:%S"),res,txt])
        self.log_model.append([dt.strftime("%Y-%m-%d %H:%M:%S"), res, txt])
        self.btn_save_log.set_sensitive(True)

    def on_log_datetime_clicked(self, col):
        pass

    def on_btn_repeat_toggled(self, btn):
        pass

    def on_btn_save_log_clicked(self, btn):
        self.on_save_activate(None)

    def on_save_activate(self, mitem):
        if self.report_filename == "":
            return self.on_save_as_activate(mitem)

        self.save_report_to_file(self.report_filename)

    def on_save_as_activate(self, mitem):
        dlg = gtk.FileChooserDialog(_("Save file"), action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dlg.set_select_multiple(False)
        f = self.tfile.split('.')
        fname = "%s.report.txt" % (f[0])
        dlg.set_current_name(fname)
        res = dlg.run()
        dlg.hide()

        if res == gtk.RESPONSE_OK:
            self.report_filename = dlg.get_filename()
            self.save_report_to_file(self.report_filename)

    def save_report_to_file(self, filename):
        out = open(filename, "w")
        it = self.log_model.get_iter_first()
        while it is not None:
            s = "%19s|%10s|%s\n" % (self.log_model.get_value(it, lid.dt), self.log_model.get_value(it, lid.res),
                                    self.log_model.get_value(it, lid.txt))
            out.write(s)
            it = self.log_model.iter_next(it)
        out.close()
        self.btn_save_log.set_sensitive(False)

    def on_mi_save_scenario_activate(self, mitem):
        dlg = self.builder.get_object("saveQueryDialog")
        res = dlg.run()
        dlg.hide()
        if res != dlg_RESPONSE_OK:
            return

        # проходим по всему дереву и сохраняем ВСЕ(!) xml-ки...
        saved_xml = dict()
        it = self.model.get_iter_first()
        self.save_xml(it, saved_xml)
        #print "**SAVED XML: %s"%str(saved_xml)

    def save_xml(self, it, saved_xml):

        while it is not None:
            xml = self.model.get_value(it, gfid.xml)
            if xml not in saved_xml:
                xml.save(xml.fname, True, True)
                saved_xml[xml.fname] = xml

            c_iter = self.model.iter_children(it)
            if c_iter != None:
                self.save_xml(c_iter, saved_xml)

            it = self.model.iter_next(it)

    def on_logview_press_event(self, object, event):

        if event.button == 3:
            self.logview_popup.popup(None, None, None, event.button, event.time)
            return False

        #        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:

        return False

    def on_mi_logview_clean_activate(self, menuitem):
        self.log_model.clear()

    def on_mi_logview_save_activate(self, mitem):
        self.on_save_activate(mitem)

    def set_testlist_element(self, val):
        if val == None:
            val = ""

        #print "select val: %s"%val
        cbox = self.editor_ui.get_object("testlist")
        model = cbox.get_model()
        it = model.get_iter_first()
        while it is not None:
            if val.upper() == str(model.get_value(it, 0)).upper():
                cbox.set_active_iter(it)
                return
            it = model.iter_next(it)

        cbox.set_active_iter(model.get_iter_first())

    def on_testlist_changed(self, cbox):
        # цель подсветить ту область настроек, которые относятся к выбранному виду теста
        # функция пробегает по списку "видов тестов"(см. editor.ui)
        # скрывает все "невыбранные" и делает show только того, который выбран
        model = cbox.get_model()
        it = model.get_iter_first()
        sel_name = model.get_value(cbox.get_active_iter(), 0)
        widget = model.get_value(cbox.get_active_iter(), 1)
        self.editor = None
        #        print "********* TEST CHANGED: %s"%sel_name
        while it is not None:
            ename = model.get_value(it, 0)
            widget = model.get_value(it, 1)
            if widget and widget.get_name() != "dummy":
                if ename == sel_name:
                    self.editor = widget
                    xmlnode = self.fmodel.get_value(self.edit_iter, gfid.xmlnode)
                    t = self.fmodel.get_value(self.edit_iter, gfid.etype)
                    if t == tt.Link or t == tt.Outlink:
                        xmlnode = self.fmodel.get_value(self.edit_iter, gfid.link_xmlnode)
                    xml = self.fmodel.get_value(self.edit_iter, gfid.xml)
                    self.player.init_config(xml)
                    config = self.player.get_item_config(xmlnode)
                    self.editor.init(xmlnode, config, self.dlg_xlist, xml)
                    widget.show()
                else:
                    widget.hide()

            it = model.iter_next(it)

    def on_mi_edit_scenario_activate(self, mitem):
        #seditor = ScenarioParamEditor(self.editor_ui)
        res = self.sceditor.run(self.tsi, self.player)
        if res != dlg_RESPONSE_OK:
            return

    def load_editor_modules(self):
        ebox = self.editor_ui.get_object("editor_vbox")
        cbox = self.editor_ui.get_object("testlist")
        #emodel = cbox.get_model()
        emodel = gtk.ListStore(str, object, str)
        cbox.set_model(emodel)
        # default value
        dummy = gtk.HBox()
        dummy.set_name("dummy")
        emodel.append(["UNKNOWN TYPE", dummy, ""])

        modlist = []
        self.emodules = dict()
        sys.path.append(self.moddir[:-1])
        for name in os.listdir(self.moddir):
            if name.startswith('editor_') == False or name.endswith('.py') == False:
                continue
            modlist.append(name)
            m = __import__(name[:-3], globals())
            self.emodules[name] = m

        for n in modlist:
            m = self.emodules[n]
            face = m.create_module(self.moddir)
            ebox.add(face)
            face.hide()
            emodel.append([m.module_name(), face, face.get_etype()])

    def on_about_activate(self, mi):
        self.dlg_about.run()
        self.dlg_about.hide()


if __name__ == "__main__":

    try:
        player = guiTestSuitePlayer()
        gtk.main()
        exit(0)

    except TestSuiteException, e:
        print "(guiTestSuiteXMLPlayer): catch exception: " + str(e.getError)
    except UException, e:
        print "(guiTestSuiteXMLPlayer): catch exception: " + str(e.getError)

    exit(1)