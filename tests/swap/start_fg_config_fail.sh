#!/bin/sh

START=uniset-start.sh

${START} -f ./TestSuiteXMLPlayer.py --testfile tests.xml --show-test-log --show-action-log --show-result-report $*

# --unideb-add-levels info,warn,crit
