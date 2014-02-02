#!/bin/sh

START=uniset-start.sh

${START} -f ./TestSuiteXMLPlayer.py --confile configure.xml --testfile tests.xml --show-test-log --show-actions-log --show-result-report --test-name Test_N3

# --unideb-add-levels info,warn,crit
