#!/bin/sh

START=uniset2-start.sh

${START} -f uniset2-smemory --smemory-id SharedMemory1 --confile configure2.xml $*
#--unideb-add-levels info,warn,crit
