#!/bin/sh

START=uniset2-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile c4@configure.xml,c2@configure2.xml --testfile tests.xml --log-show-tests --log-show-actions --junit j1.xml $*

# --unideb-add-levels info,warn,crit
