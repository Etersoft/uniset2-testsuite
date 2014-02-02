#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import os
import time
import gobject
import gtk
from TestSuiteGlobal import *
from ProcessMonitor import *

# ---------------------------------------------------------
#class GtkProcessMonitor(gobject.GObject):
class GtkProcessMonitor():
  
     def __init__(self, plist=[], check_msec=2000,after_run_pause=0):
        
        #gobject.GObject.__init__(self)
        self.init(plist,check_msec,after_run_pause)

     def init(self, plist, check_msec,after_run_pause):
        self.plist = plist
        self.check_msec = check_msec
        self.active = False
        self.term_flag = False
        self.term_callback = None
        self.runproc_callback = None
        self.tmr = None
        self.after_run_pause = after_run_pause

     def addChild(self, ch):
#        print "ProcessMonitor: add child " + ch.name
        if ch not in self.plist:
           self.plist.append(ch)

     def setTerminateCallback(self, callback):
        self.term_callback = callback

     def setRunProgressCallback(self, callback):
        self.runproc_callback = callback

     def run(self, stop_flag):
        self.active = True
        self.term_flag = False
        self.tmr = None
        clist = []

        run_proc_max = len(self.plist)
        run_proc = 0.0

        if self.runproc_callback:
           self.runproc_callback(run_proc,"")

        for p in self.plist:
            try:
                # run process calback
                if self.runproc_callback:
                   text = "Running %s..."%p.name
                   self.runproc_callback(fcalibrate(run_proc,0.0,run_proc_max,0.0,1.0),text)
                   while gtk.events_pending():
                       gtk.main_iteration()

                p.run()
                clist.append(p.popen)
                run_proc += 1

                # run process calback
                if self.runproc_callback:
                   text = "Run %s [OK]"%p.name
                   self.runproc_callback(fcalibrate(run_proc,0.0,run_proc_max,0.0,1.0),text)
                   while gtk.events_pending():
                       gtk.main_iteration()

            except OSError, e:
               err = "[FAILED]: (ProcessMonitor): run '%s' failed.(cmd='%s' error: (%d)%s)."%(p.name,p.cmd,e.errno,e.strerror)
               if p.ignore_run_failed == False and self.term_flag == False:
                  print err
                  print "(ProcessMonitor): ..terminate all.."
                  for p in self.plist:
                      p.stop()

                  self.active = False
                  if self.term_callback:
                     self.term_callback(err)

                  raise TestSuiteException(err)

        print "************ RUN process OK ********"
        # запускаем Gtk-таймер для отслеживания процессов
        self.tmr = gobject.timeout_add(self.check_msec,self.check_timer)
        return True

     def check_timer(self):
         for p in self.plist:
             if p.runing and p.popen.poll() != None:
                p.runing = False
                if p.ignore_terminated == False and self.term_flag == False:
                   err = "[FAILED]:(ProcessMonitor):  Process '%s' terminated..(retcode=%d)"%(p.name,p.popen.poll())
                   print err

                   #raise TestSuiteException(err)
                   print "(ProcessMonitor): ..terminate all.."
                   for p in self.plist:
                       p.stop()

                   self.active = False
                   if self.term_callback:
                      self.term_callback(err)

                   return False

             if self.term_flag == True or self.active == False:
                print "***** break process monitor ***"
                return False
           
         if self.term_flag == True or self.active == False:
            print "***** break process monitor ***"
            return False
           
         return True
     
     def m_start(self,stop_flag):
          return self.run(stop_flag)
     
     def m_finish(self):
         if self.active == False:
            return	  

         self.term_flag = True

         if self.tmr:
            gobject.source_remove(self.tmr)

         for p in self.plist:
             print "terminate '%s'  pid=%d"%(str(p.cmd),p.popen.pid)
             try:
                p_pid = p.popen.pid
                p.stop()
                waitncpid(p_pid)
             except OSError, e:
                print "terminate failed: (%d)%s"%(e.errno,e.strerror)

         #wait_childs()
         self.active = False
# ---------------------------------------------------------  
