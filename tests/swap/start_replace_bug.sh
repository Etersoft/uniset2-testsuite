#!/bin/sh

uniset2-start.sh -f python ./TestSuiteXMLPlayer.py --confile configure.xml --testfile tests-replace-bug.xml $* --show-result-report --show-action-log --show-test-log --ignore-run-list

# --unideb-add-levels info,warn,crit
