#!/bin/sh

START=uniset2-start.sh

UNISET_TESTSUITE_DATADIR=./ ${START} -f python ./TestSuiteXMLPlayer.py --confile configure.xml --testfile compare_tests.xml \
--log-show-tests --log-show-actions $*

# --unideb-add-levels info,warn,crit
