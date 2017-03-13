#!/bin/sh

START=uniset2-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile configure.xml --testfile check_scenario_tests.xml \
--log-show-tests --log-show-actions --show-test-tree --play-tags "#tag1#tag3#long_tag_name" $*
