#!/bin/sh

START=uniset-start.sh

${START} -f uniset-smemory --smemory-id SharedMemory1 --confile configure2.xml $*
#--unideb-add-levels info,warn,crit
