#!/bin/sh

START=uniset2-start.sh

${START} -f python ./TestSuiteXMLPlayer.py --confile configure.xml --testfile check_tests.xml --log-show-tests --log-show-actions $*
