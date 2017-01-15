#!/bin/sh

python ./TestSuiteXMLPlayer.py --testfile snmp_tests.xml --show-test-log --show-action-log --junit j1.xml --show-result-report $*
