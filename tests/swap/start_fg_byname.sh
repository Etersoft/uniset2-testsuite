#!/bin/sh

START=uniset2-start.sh

${START} -f ./TestSuiteXMLPlayer.py --confile configure.xml --testfile tests.xml --log-show-tests --log-show-actions --junit j.xml --test-name "tname=less,tname=great" $*

# --unideb-add-levels info,warn,crit
