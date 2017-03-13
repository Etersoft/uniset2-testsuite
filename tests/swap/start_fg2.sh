#!/bin/sh

START=uniset-start.sh

${START} -f ./TestSuiteXMLPlayer.py --confile configure2.xml --testfile tests.xml --log-show-tests --log-show-actions --junit j.xml $*

# --unideb-add-levels info,warn,crit
