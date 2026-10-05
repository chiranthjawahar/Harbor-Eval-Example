#!/bin/bash
set -u

mkdir -p /logs/verifier
python3 - <<'EOF' > /logs/verifier/test-stdout.txt 2>&1
import json
from pathlib import Path
import sys

rca_path = Path("/workspace/sla_breach_rca.json")
ans_path = Path("/workspace/answer.md")
if not rca_path.exists():
    print("FAIL: /workspace/sla_breach_rca.json missing")
    sys.exit(1)
if not ans_path.exists() or not ans_path.read_text().strip():
    print("FAIL: /workspace/answer.md missing or empty")
    sys.exit(1)

data = json.loads(rca_path.read_text())
assert sorted(data["breached_ticket_ids"]) == ["TKT-901", "TKT-904"], f"Wrong tickets: {data}"
assert data["total_enterprise_arr_at_risk_usd"] == 1450000, f"Wrong ARR: {data}"
team = data["by_owning_team"]["Auth-Platform"]
assert team["arr_at_risk_usd"] == 1450000
assert team["incident_id"] == "INC-402"
assert team["remediation_eta"] == "2026-10-15"
print("PASS: All SLA breach RCA checks succeeded.")
EOF

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
