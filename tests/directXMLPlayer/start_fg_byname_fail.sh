#!/bin/sh

START=uniset-start.sh

${START} -f ./TestSuiteXMLPlayer.py --confile configure.xml --testfile test_by_name_failscript.xml --show-test-log --show-action-log --show-result-report --junit j.xml --test-name "tname=t5" $*

# --unideb-add-levels info,warn,crit
