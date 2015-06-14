#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

sys.path.append('./.libs/')
sys.path.append('../../lib/')
sys.path.append('../../lib/pyUniSet/.libs/')
sys.path.append('../../lib/pyUniSet/')

from TestSuiteInterface import *
from TestSuiteGlobal import *

if __name__ == "__main__":

    ts = TestSuiteInterface()
    try:
        ts.init_testsuite("configure.xml", True)
        ts.set_ignorefailed(True)
        ts.isFalse(101)
        ts.isEqual(101, 0)
        ts.isTrue(101)

        ts.set_logfile("testlog.txt", True)
        ts.set_ignorefailed(False)
        ts.isFalse(101)
        ts.isEqual(101, 0)
        ts.isTrue(101)

    # ts.set_notimestamp(True)

    except TestSuiteException, e:
        print "(testTS): catch exception: " + str(e.getError)
    except UException, e:
        print "(testTS): catch exception: " + str(e.getError())
	