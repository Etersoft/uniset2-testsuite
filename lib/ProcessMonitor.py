#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import threading
from subprocess import Popen

from TestSuiteGlobal import *


# ---------------------------------------------------------
class ChildProcess():
    def __init__(self, xmlnode):

        self.xmlnode = xmlnode
        self.cmd = []
        self.cmd.append(to_str(xmlnode.prop('script')))
        self.cmd = self.cmd + to_str(xmlnode.prop('args')).split(" ")
        self.ignore_terminated = to_int(xmlnode.prop('ignore_terminated'))
        self.ignore_run_failed = to_int(xmlnode.prop('ignore_run_failed'))
        self.after_run_pause = to_int(xmlnode.prop('after_run_pause')) / 1000.0
        self.silent_mode = to_int(xmlnode.prop('silent_mode'))
        self.logfilename = xmlnode.prop('logfile')
        self.logfile = None
        self.popen = None
        self.name = to_str(xmlnode.prop('name'))
        if self.name == "":
            scriptname = to_str(xmlnode.prop("script"))
            self.name = os.path.basename(scriptname)

        self.chdir = xmlnode.prop('chdir')
        self.runing = False

    def run(self, waitfinish=False):
        # print "run child process: " + self.name
        #        print "*************** cmd: " + str(self.cmd)
        sout = None
        serr = None
        if self.silent_mode:
            nul_f = open(os.devnull, 'w')
            sout = nul_f
            serr = nul_f

        if self.logfilename is not None:
            self.logfile = open(self.logfilename, 'w')
            sout = self.logfile
            serr = self.logfile

        self.popen = Popen(self.cmd, preexec_fn=os.setsid, cwd=self.chdir, stdout=sout, stderr=serr)
        self.runing = True
        if self.after_run_pause > 0:
            time.sleep(self.after_run_pause)

        if waitfinish == True:
            self.popen.wait()

    def stop(self):
        if self.popen and self.popen.poll() is None:
            # self.popen.terminate()
            os.killpg(self.popen.pid, signal.SIGTERM)
            self.popen.wait()
            if self.logfile is not None:
                self.logfile.close()

        self.runing = False

    def kill(self):
        if self.popen and self.popen.poll() is None:
            # self.popen.kill()
            os.killpg(self.popen.pid, signal.SIGKILL)
            self.popen.wait()
            if self.logfile is not None:
                self.logfile.close()

        self.runing = False

    def wait(self):
        if self.popen and self.popen.poll() == None:
            self.popen.wait()


# ---------------------------------------------------------
def waitncpid(w_pid, timeout_sec=-1):
    """

    :rtype :
    """
    tick = timeout_sec
    while True:
        try:
            # print "******* wait terminate child pid=%d"%w_pid
            # os.kill(w_pid, 0)
            os.waitpid(w_pid, 0)
            time.sleep(1)
            if timeout_sec > 0:
                if tick <= 0:
                    break
                tick -= 1

        except OSError, KeyboardInterrupt:
            break
            # print "******* wait terminate child pid=%d [OK]"%w_pid


# ---------------------------------------------------------
def wait_childs(timeout_sec=-1):
    tick = timeout_sec
    while True:
        try:
            # print "******* wait terminate ALL childs"
            os.wait()
            time.sleep(1)
            if timeout_sec > 0:
                if tick <= 0:
                    break
                tick = tick - 1
        except OSError, KeyboardInterrupt:
            break
            # print "******* wait terminate ALL childs [OK]"


# ---------------------------------------------------------
class MonitorThread(threading.Thread):
    def __init__(self, plist_=None, check_msec=2000):

        if not plist_:
            plist_ = []
        threading.Thread.__init__(self)
        self.plist = plist_
        self.check_sec = check_msec / 1000.0
        self.active = False
        self.term_flag = False
        self.run_event = threading.Event()
        self.parent_pid = None
        self.pid = None

    def run(self):
        self.run_event.clear()
        self.active = True
        self.term_flag = False
        self.pid = os.getpid()
        clist = []
        for p in self.plist:
            try:
                p.run()
                clist.append(p.popen)
            except (OSError, KeyboardInterrupt), e:
                err = '[FAILED]: (ProcessMonitor): run \'%s\' failed.(cmd=\'%s\' error: (%d)%s).' % (
                p.name, p.cmd, e.errno, e.strerror)
                if p.ignore_run_failed is False and self.term_flag is False:
                    print err
                    print '(ProcessMonitor): ..terminate all..'
                    for pp in self.plist:
                        if pp.popen:
                            p_pid = pp.popen.pid
                            pp.stop()
                            waitncpid(p_pid)

                    self.active = False
                    os.kill(self.parent_pid, signal.SIGTERM)
                    return

        self.run_event.set()

        # print "Run monitor process..."
        while self.active:
            for p in self.plist:
                if p.runing and p.popen.poll() is not None:
                    p.runing = False
                    if p.ignore_terminated is False and self.term_flag is False:
                        err = '[FAILED]:(ProcessMonitor):  Process \'%s\' terminated..(retcode=%d)' % (
                            p.name, p.popen.poll())
                        print err
                        # raise TestSuiteException(err)
                        print '(ProcessMonitor): ..terminate all..'
                        for pp in self.plist:
                            if pp.popen:
                                p_pid = pp.popen.pid
                                pp.stop()
                                waitncpid(p_pid)

                        self.active = False
                        os.kill(self.parent_pid, signal.SIGTERM)
                        return

                if self.term_flag is True or self.active is False:
                    break

            if self.term_flag is True or self.active is False:
                break

            time.sleep(self.check_sec)

    def m_start(self, p_pid):
        self.parent_pid = p_pid
        self.run_event.clear()
        self.start()
        self.run_event.wait()

    def m_stop(self):
        if not self.active:
            return
        # print "****************** m_stop"
        self.term_flag = True
        for p in self.plist:
            # print "terminate " + str(p.cmd)
            try:
                if p.popen:
                    p_pid = p.popen.pid
                    p.stop()
                    waitncpid(p_pid)
            except (OSError, KeyboardInterrupt), e:
                print 'terminate failed: (%d)%s' % (e.errno, e.strerror)

        self.active = False
        self.join()

    def m_finish(self):
        if not self.active:
            return
        self.term_flag = True
        for p in self.plist:
            try:
                if p.popen:
                    print 'terminate \'%s\'  pid=%d' % (str(p.cmd), p.popen.pid)
                    p_pid = p.popen.pid
                    p.stop()
                    waitncpid(p_pid)
            except (OSError, KeyboardInterrupt), e:
                print 'terminate failed: (%d)%s' % (e.errno, e.strerror)

        self.active = False
        self.join()


# ---------------------------------------------------------
class ProcessMonitor():
    def __init__(self, plist_=None, check_msec=2000, after_run_pause=0):

        """

        :type check_msec: value of miliseconds
        """
        if not plist_:
            plist_ = []
        self.plist = plist_
        self.check_msec = check_msec
        self.active = False
        self.thr = None
        self.after_run_pause = after_run_pause

    def addChild(self, ch):
        # print "ProcessMonitor: add child " + ch.name
        if ch not in self.plist:
            self.plist.append(ch)

    def start(self):
        if len(self.plist) <= 0:
            return

        if not self.active:
            self.thr = MonitorThread(self.plist, self.check_msec)
            self.thr.m_start(os.getpid())  # запуск с ожиданием запуска всех
            self.active = True
            if self.after_run_pause > 0:
                # print "******** PAUSE AFTER RUN " + str(self.after_run_pause)
                time.sleep(self.after_run_pause)
            else:
                time.sleep(1)

    def stop(self):
        if not self.active:
            return
        self.active = False
        self.thr.m_stop()
        self.thr = None

    def finish(self):
        if not self.active:
            return

        self.active = False
        if self.thr:
            self.thr.m_finish()
            self.thr = None

    def join(self):
        if self.thr:
            self.thr.join()

# ---------------------------------------------------------
