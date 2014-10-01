#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk
# pygtk.require("2.0")

import gtk

PADDING = 8


class mytest:
    """
    """

    def __init__(self):
        self.w = gtk.Window()

        self.b = gtk.Button('dummy button')
        self.e = gtk.Entry()

        self.tv = gtk.TreeView()
        self.ls = gtk.ListStore(str, str)

        cell1 = gtk.CellRendererText()
        cell1.set_property('editable', True)
        cell1.connect('edited', self.beep)
        col1 = gtk.TreeViewColumn('entry')
        col1.pack_start(cell1, True)
        col1.add_attribute(cell1, 'text', 0)

        cell2 = gtk.CellRendererCombo()
        cell2.set_property('editable', True)
        self.combols = gtk.ListStore(str, str)
        cell2.set_property('model', self.combols)
        cell2.set_property('text-column', 0)
        cell2.connect('edited', self.beep)
        col2 = gtk.TreeViewColumn('select')
        col2.pack_start(cell2, True)
        col2.add_attribute(cell2, 'text', 1)

        self.tv.append_column(col1)
        self.tv.append_column(col2)

        self.tv.set_model(self.ls)

        vbox = gtk.VBox()
        vbox.pack_start(self.b, False, True, PADDING)
        vbox.pack_start(self.e, False, True, PADDING)
        vbox.pack_start(self.tv, False, True, PADDING)
        self.w.add(vbox)

        self.w.show_all()

        self.popolate_list_store()


    def popolate_list_store(self):
        self.combols.append(('1', 'uno'))
        self.combols.append(('2', 'due'))

        self.ls.append(('qwe', '1'))
        self.ls.append(('qwerty', '2'))


    def beep(self, widget, t, i):
        print "\a"


def main():
    gtk.main()
    return 0


if __name__ == "__main__":
    app = mytest()
    main()
