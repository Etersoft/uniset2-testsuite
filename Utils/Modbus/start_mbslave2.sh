#!/bin/sh

ADDR=0x02
[ -n "$1" ] && ADDR="$1"

uniset2-mbtcpserver-echo -i localhost -p 2049 -a $ADDR
