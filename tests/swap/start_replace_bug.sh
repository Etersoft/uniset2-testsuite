#!/bin/sh

uniset2-start.sh -f python ./TestSuiteXMLPlayer.py --confile configure.xml --testfile tests-replace-bug.xml $* --log-show-actions --log-show-tests --ignore-run-list

# --unideb-add-levels info,warn,crit
