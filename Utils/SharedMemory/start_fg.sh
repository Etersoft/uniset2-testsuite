#!/bin/sh

START=uniset2-start.sh

#echo `pwd`
${START} -f uniset2-smemory --smemory-id SharedMemory1 $*
#--unideb-add-levels info,warn,crit
