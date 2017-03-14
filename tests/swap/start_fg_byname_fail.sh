#!/bin/sh

START=uniset-start.sh

${START} -f ./TestSuiteXMLPlayer.py --confile configure.xml --testfile test_by_name_failscript.xml --check-scenario --log-show-tests --log-show-actions --junit j.xml --test-name "tname=t5" $*

# --unideb-add-levels info,warn,crit
