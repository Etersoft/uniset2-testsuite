#!/bin/sh

function run_test()
{
	RET=0
	$1 1>/dev/null 2>/dev/null || RET=1

	if [ "$RET" == 1 ]; then
		echo "[FAILED]: $1"
	else
		echo "[  OK  ]: $1"
	fi
}

run_test ./test-check.sh
run_test ./test-compare.sh
run_test ./test-snmp.sh
run_test ./test-multi.sh
run_test ./test-scripts-interface.sh
