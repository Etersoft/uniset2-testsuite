#!/bin/sh

START=uniset2-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile configure.xml --testfile check_scenario_conf_tests.xml \
--show-test-log --show-action-log --junit j1.xml --show-result-report --check-scenario --check-scenario-ignore-failed $*

# --unideb-add-levels info,warn,crit
