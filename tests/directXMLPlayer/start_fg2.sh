#!/bin/sh

START=uniset-start.sh

${START} -f ./TestSuiteXMLPlayer.py --confile configure2.xml --testfile tests.xml --show-test-log --show-actions-log --show-result-report --junit j.xml $*

# --unideb-add-levels info,warn,crit
