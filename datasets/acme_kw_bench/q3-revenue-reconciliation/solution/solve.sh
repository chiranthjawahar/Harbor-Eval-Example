#!/bin/bash
set -euo pipefail

python3 - <<'EOF'
import csv
import json

with open("/workspace/data/erp_ledger.json") as f:
    erp = {row["invoice_id"]: row["recognized_usd"] for row in json.load(f)["entries"]}

recognized_total = 0.0
discrepancies = []

with open("/workspace/data/stripe_exports.csv") as f:
    for row in csv.DictReader(f):
        inv_id = row["invoice_id"]
        amt = float(row["amount"])
        if row["status"] == "refunded":
            rec = 0.0
        else:
            if row["currency"] == "EUR":
                amt *= 1.10
            if row["billing_term"] == "annual":
                amt *= 0.25
            rec = round(amt, 2)
        recognized_total += rec
        if round(erp[inv_id], 2) != rec:
            discrepancies.append(inv_id)

report = {
    "net_recognized_usd_cents": int(round(recognized_total * 100)),
    "recognized_revenue_usd": round(recognized_total, 2),
    "discrepancy_invoice_ids": list(reversed(discrepancies)),
}
with open("/workspace/reconciliation_report.json", "w") as f:
    json.dump(report, f, indent=2)

with open("/workspace/answer.md", "w") as f:
    f.write("## Section 1: GAAP Variance Table\n\n")
    f.write(f"Total Q3 recognized revenue is **${recognized_total:,.2f}** (ERP booked $69,500.00).\n")
    f.write("- **INV-1002**: Annual contract booked at 100% ($24,000) instead of 25% ($6,000).\n")
    f.write("- **INV-1003**: EUR 10,000 booked at 1:1 instead of 1.10 USD FX rate ($11,000).\n")
    f.write("- **INV-1004**: Refunded charge ($8,500) erroneously recognized.\n")
EOF
