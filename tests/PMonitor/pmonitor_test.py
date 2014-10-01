#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ProcessMonitor import *

if __name__ == "__main__":

    mp = ProcessMonitor()

    try:
        xml = UniXML("tests.xml")
        node = xml.findNode(xml.getDoc(), "RunList")[0]
        node = xml.firstNode(node.children)
        while node != None:
            # print "run node: " + str(node)
            c = ChildProcess(node)
            mp.addChild(c)
            node = xml.nextNode(node)

        mp.start()
        print "Wait child processes"
        time.sleep(1)
        print "Stop processes"
        mp.stop()
        time.sleep(3)
        print "Kill processes"
        time.sleep(3)

        print "Restart processes"
        mp.start()
        time.sleep(5)
        print "Stop processes"
        mp.stop()

        mp.join()
        print "Monit proc terminated"

    except OSError, e:
        print("Execution failed...")
    except TestSuiteException, e:
        print e.getError()

    finally:
        mp.finish()
       
       