#!/bin/sh

START=uniset2-start.sh

${START} -f ./TestSuiteXMLPlayer.py --confile configure.xml --testfile test-script.xml --show-test-log --show-actions-log --show-result-report $*

# --unideb-add-levels info,warn,crit
