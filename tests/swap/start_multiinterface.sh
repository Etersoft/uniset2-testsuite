#!/bin/sh

uniset2-start.sh -f ./TestSuiteXMLPlayer.py --confile configure.xml --testfile multi_interface.xml --log-show-tests --log-show-actions --junit j1.xml

#--dlog-add-levels any --unideb-add-levels any $*


# --unideb-add-levels info,warn,crit
