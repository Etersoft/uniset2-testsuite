#!/bin/sh

START=uniset-start.sh

#echo `pwd`
${START} -f uniset-smemory --smemory-id SharedMemory1 $*
#--unideb-add-levels info,warn,crit
