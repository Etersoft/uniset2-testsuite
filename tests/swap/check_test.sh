#!/bin/sh

./TestSuiteXMLPlayer.py --confile Conf/configure.xml --testfile All_tests.xml --check-scenario --show-action-log --show-test-log $*

# --unideb-add-levels info,warn,crit
