#!/bin/sh

START=uniset-start.sh
${START} -f uniset-admin --confile configure2.xml $* 
#"./kater-admin --`basename $0 .sh` $1 $2 $3 $4 --confile ./configure.xml --id-from-config"
#uniset-admin --`basename $0 .sh` --confile ./configure.xml $1 $2 $3 $4
