#!/bin/sh

START=uniset-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile c4@configure.xml,c2@configure2.xml --testfile tests_repl.xml --junit j2.xml $*

# --unideb-add-levels info,warn,crit
