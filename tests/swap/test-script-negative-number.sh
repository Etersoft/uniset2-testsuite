#!/bin/sh

echo "TEST SCRIPT: $*"

echo  "SHOW ENV VARIABLES: .."
env | grep MyTEST
env | grep UNISET_TESTSUITE

echo "TEST_SCRIPT_RESULT: -20"

