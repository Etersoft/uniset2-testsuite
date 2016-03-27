#!/bin/sh

START=uniset-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile configure.xml --testfile compare_tests.xml \
--show-test-log --show-action-log --junit j1.xml --show-result-report $*

# --unideb-add-levels info,warn,crit
