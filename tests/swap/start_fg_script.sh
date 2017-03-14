#!/bin/sh

START=uniset2-start.sh

${START} -f ./TestSuiteXMLPlayer.py --confile configure.xml --testfile test-script.xml --log-show-tests --log-show-actions $*

# --unideb-add-levels info,warn,crit
