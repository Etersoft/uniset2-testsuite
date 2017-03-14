#!/bin/sh

./TestSuiteXMLPlayer.py --confile Conf/configure.xml --testfile All_tests.xml --check-scenario --log-show-actions --log-show-tests $*

# --unideb-add-levels info,warn,crit
