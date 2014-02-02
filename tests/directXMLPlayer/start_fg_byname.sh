#!/bin/sh

START=uniset-start.sh

${START} -f ./TestSuiteXMLPlayer.py --confile configure.xml --testfile tests.xml --show-test-log --show-actions-log --show-result-report --test-name num=0

# --unideb-add-levels info,warn,crit
