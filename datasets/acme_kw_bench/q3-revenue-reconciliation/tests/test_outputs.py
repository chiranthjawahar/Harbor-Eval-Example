"""Fair, specification-aligned verifier for Task 1: Q3 Recognized Revenue Reconciliation.

FIXES APPLIED:
1. Grades `recognized_revenue_usd` (in USD dollars) as documented in `instruction.md`.
2. Checks `discrepancy_invoice_ids` as an order-independent set (`{"INV-1002", "INV-1003", "INV-1004"}`).
3. Verifies that `/workspace/answer.md` mentions each discrepancy invoice ID without enforcing
   an undocumented model-specific markdown heading.
"""

import json
from pathlib import Path
import sys


def main() -> None:
  report_path = Path("/workspace/reconciliation_report.json")
  answer_path = Path("/workspace/answer.md")

  if not report_path.exists():
    print("FAIL: /workspace/reconciliation_report.json missing")
    sys.exit(1)
  if not answer_path.exists():
    print("FAIL: /workspace/answer.md missing")
    sys.exit(1)

  data = json.loads(report_path.read_text())
  rev = float(data.get("recognized_revenue_usd", -1))
  if abs(rev - 44000.0) > 0.01:
    print(f"FAIL: Expected recognized_revenue_usd == 44000.0, got {rev}")
    sys.exit(1)

  expected_ids = {"INV-1002", "INV-1003", "INV-1004"}
  actual_ids = set(data.get("discrepancy_invoice_ids", []))
  if actual_ids != expected_ids:
    print(
        f"FAIL: Expected discrepancy_invoice_ids {expected_ids}, got {actual_ids}"
    )
    sys.exit(1)

  answer_text = answer_path.read_text()
  for inv_id in expected_ids:
    if inv_id not in answer_text:
      print(f"FAIL: answer.md does not mention discrepancy invoice {inv_id}")
      sys.exit(1)

  print("PASS: All functional reconciliation checks succeeded.")


if __name__ == "__main__":
  main()
