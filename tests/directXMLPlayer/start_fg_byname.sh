#!/bin/sh

START=uniset2-start.sh

${START} -f ./TestSuiteXMLPlayer.py --confile configure.xml --testfile tests.xml --show-test-log --show-actions-log --show-result-report --junit j.xml --test-name "tname=less,tname=great" $*

# --unideb-add-levels info,warn,crit
