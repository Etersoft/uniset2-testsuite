#!/bin/sh

START=uniset2-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile configure.xml --testfile check_scenario_tests.xml \
--show-test-log --show-action-log --show-result-report --show-test-tree --play-tags "#tag1#tag3#long_tag_name" $*

# --unideb-add-levels info,warn,crit
