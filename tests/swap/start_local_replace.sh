#!/bin/sh

uniset2-start.sh -f python ./TestSuiteXMLPlayer.py --confile configure.22220.xml --testfile Test_replace_local.xml $* --show-result-report --show-action-log --show-test-log --default-timeout 10000 --default-check-pause 200 --ignore-run-list

# --unideb-add-levels info,warn,crit
