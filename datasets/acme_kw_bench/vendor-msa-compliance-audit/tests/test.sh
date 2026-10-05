#!/bin/bash

mkdir -p /logs/verifier
pip install pyyaml > /logs/verifier/test-stdout.txt 2>&1

python3 - <<'EOF' >> /logs/verifier/test-stdout.txt 2>&1
import json, pathlib, sys
p = pathlib.Path("/app/compliance_findings.json")
if not p.exists():
    print("FAIL: /app/compliance_findings.json does not exist!")
    sys.exit(1)
data = json.loads(p.read_text())
assert data["overall_status"] == "REJECT"
assert sorted(data["violated_clauses"]) == ["SEC-11.3", "SEC-14.1", "SEC-8.1"]
print("PASS")
EOF

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
