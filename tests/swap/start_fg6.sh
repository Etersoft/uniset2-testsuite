#!/bin/sh

START=uniset-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --testfile fail_tests.xml --log-show-tests --log-show-actions --junit j1.xml $*

# --unideb-add-levels info,warn,crit
