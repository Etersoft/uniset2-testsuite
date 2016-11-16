#!/bin/sh

uniset2-start.sh -f ./TestSuiteXMLPlayer.py --confile configure.xml --testfile multi_interface.xml --show-test-log --show-action-log --show-result-report --junit j1.xml

#--dlog-add-levels any --unideb-add-levels any $*


# --unideb-add-levels info,warn,crit
