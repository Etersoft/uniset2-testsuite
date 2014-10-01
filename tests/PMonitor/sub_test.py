#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import signal
import threading
from subprocess import Popen


class ChildProcess():
    def __init__(self, xmlnode):
        self.cmd = ""
        self.args = ""
        self.ignore_terminated = False
        self.popen = None

    def run(self):
        print "run child: " + str(self.cmd)
        self.popen = Popen([self.cmd, self.args])

    def stop(self):
        if self.popen and self.popen.poll() == None:
            self.popen.kill()


class MonitProcess(threading.Thread):
    def __init__(self, plist):

        threading.Thread.__init__(self)
        self.plist = plist

    def run(self):
        clist = []
        for p in self.plist:
            try:
                p.run()
                clist.append(p.popen)
            except OSError as e:
                print("child exception...")
                if p.ignore_terminated == False:
                    raise e

        print "Monit proc..."
        while len(clist) > 0:
            clist = [x for x in clist if x.poll() == None]
            print "wait..."
            time.sleep(1)

        print "ALL child terminated..."

    def stop_all(self):
        for p in self.plist:
            print "terminate " + str(p.cmd)
            p.stop()


if __name__ == "__main__":

    try:
        print "START TEST"

        p1 = ChildProcess(None)
        p1.cmd = "./script1.sh"
        p1.args = "arg1 arg2 arg3"

        p2 = ChildProcess(None)
        p2.cmd = "./script2.sh"
        p2.args = "arg1 arg2 arg3"

        p3 = ChildProcess(None)
        p3.cmd = "./script3.sh"
        p3.args = "arg1 arg2 arg3"

        mp = MonitProcess([p1, p2, p3])
        mp.start()
        mp.join()
        print "Monit proc terminated"

    except OSError, e:
        print("Execution failed...")

    finally:
        mp.stop_all()