#!/bin/bash
set -u

mkdir -p /logs/verifier
python3 /tests/test_outputs.py > /logs/verifier/test-stdout.txt 2>&1
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
