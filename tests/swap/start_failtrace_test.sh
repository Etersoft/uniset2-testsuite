#!/bin/sh

START=uniset2-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile ./configure.xml --testfile test_failtrace.xml --print-calltrace --log-show-tests --log-show-actions $*

# --unideb-add-levels info,warn,crit
