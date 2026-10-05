#!/bin/bash
# FIXED VERIFIER:
# 1. Removed `pip install pyyaml` (air-gapped verifier container has allow_internet=false).
# 2. Reads `/workspace/compliance_findings.json` matching `WORKDIR /workspace` and `instruction.md`.
set -u

mkdir -p /logs/verifier
python3 - <<'EOF' > /logs/verifier/test-stdout.txt 2>&1
import json, pathlib, sys

p = pathlib.Path("/workspace/compliance_findings.json")
ans = pathlib.Path("/workspace/answer.md")
if not p.exists():
    print("FAIL: /workspace/compliance_findings.json does not exist!")
    sys.exit(1)
if not ans.exists() or not ans.read_text().strip():
    print("FAIL: /workspace/answer.md missing or empty!")
    sys.exit(1)

data = json.loads(p.read_text())
assert data["overall_status"] == "REJECT", f"Expected REJECT, got {data.get('overall_status')}"
assert sorted(data["violated_clauses"]) == ["SEC-11.3", "SEC-14.1", "SEC-8.1"]
print("PASS: All MSA compliance checks succeeded.")
EOF

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
