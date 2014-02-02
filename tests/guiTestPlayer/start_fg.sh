#!/bin/sh

START=uniset-start.sh

#${START} -f ./guiTestSuitePlayer-gtk.py --confile configure.xml --testfile tests.runlist.xml
${START} -f ./guiTestSuitePlayer-gtk.py --confile configure.xml --testfile tests.xml
#--confile configure.xml --testfile tests.xml --show-test-log --show-actions-log --show-result-report $*
# --unideb-add-levels info,warn,crit
