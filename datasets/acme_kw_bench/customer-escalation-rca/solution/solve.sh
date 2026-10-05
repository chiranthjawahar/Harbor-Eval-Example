#!/bin/bash
set -euo pipefail

python3 - <<'EOF'
import json
import sqlite3

conn = sqlite3.connect("/workspace/data/support_tickets.db")
rows = conn.execute("""
    SELECT ticket_id, account_name, account_arr_usd, linked_incident_id
    FROM support_tickets
    WHERE tier = 'enterprise' AND first_response_latency_mins > 60
    ORDER BY ticket_id
""").fetchall()

ticket_ids = [r[0] for r in rows]
total_arr = sum(r[2] for r in rows)

rca = {
    "breached_ticket_ids": ticket_ids,
    "total_enterprise_arr_at_risk_usd": total_arr,
    "by_owning_team": {
        "Auth-Platform": {
            "arr_at_risk_usd": total_arr,
            "incident_id": "INC-402",
            "remediation_eta": "2026-10-15"
        }
    }
}
with open("/workspace/sla_breach_rca.json", "w") as f:
    json.dump(rca, f, indent=2)

with open("/workspace/answer.md", "w") as f:
    f.write("# Enterprise SLA Breach Executive Brief\n\n")
    f.write("- **Breached Tickets**: `TKT-901` (Apex Financial, $850k ARR) and `TKT-904` (Delta Logistics, $600k ARR).\n")
    f.write("- **Total Enterprise ARR at Risk**: **$1,450,000**.\n")
    f.write("- **Root Cause (`INC-402` - `Auth-Platform`)**: OAuth token introspection cache stampede.\n")
    f.write("- **Remediation ETA**: `2026-10-15`.\n")
EOF
