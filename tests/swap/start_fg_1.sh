#!/bin/sh

START=uniset2-start.sh

${START} -f uniset2-testsuite-xmlplayer --confile c4@configure.xml,c2@configure2.xml --testfile tests.xml --show-test-log --show-action-log --junit j1.xml --show-result-report $*

# --unideb-add-levels info,warn,crit
