#!/bin/sh

START=uniset-start.sh

${START} -f ./TestSuiteXMLPlayer.py --testfile tests.xml --log-show-tests --log-show-actions $*

# --unideb-add-levels info,warn,crit
