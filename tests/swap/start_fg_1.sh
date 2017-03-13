#!/bin/sh

START=uniset2-start.sh

${START} -f uniset2-testsuite-xmlplayer --confile c4@configure.xml,c2@configure2.xml --testfile tests.xml --log-show-tests --log-show-actions --junit j1.xml $*

# --unideb-add-levels info,warn,crit
