#!/bin/sh

START=uniset2-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile configure.xml --testfile check_scenario_tests.xml \
--log-show-tests --log-show-actions --junit j1.xml --check-scenario --check-scenario-ignore-failed $*

# --unideb-add-levels info,warn,crit
