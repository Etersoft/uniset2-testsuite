#!/bin/sh

START=uniset-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile c4@configure.xml,c2@configure2.xml --testfile tests.xml --show-test-log --show-action-log --junit j1.xml --show-result-report $*

# --unideb-add-levels info,warn,crit
