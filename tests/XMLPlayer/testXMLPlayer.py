#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

sys.path.append('./.libs/')
sys.path.append('../../lib/')
sys.path.append('../../lib/pyUniSet/.libs/')
sys.path.append('../../lib/pyUniSet/')

from TestSuiteXMLPlayer import *
from TestSuiteInterface import *

if __name__ == "__main__":

    ts = TestSuiteInterface()
    try:
        ts.init_testsuite("configure.xml", True)
        player = TestSuiteXMLPlayer(ts, "tests.xml")
        player.play_all()

    except TestSuiteException, e:
        print "(testXMLPLayer): catch exception: " + str(e.getError())
    except UException, e:
        print "(testXMLPlayer): catch exception: " + str(e.getError())
	