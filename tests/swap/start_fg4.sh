#!/bin/sh

START=uniset-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile c4@configure.xml,c2@configure2.xml --testfile tests_r.xml --junit j2.xml --show-result-report --show-test-log --show-action-log $*

# --unideb-add-levels info,warn,crit
