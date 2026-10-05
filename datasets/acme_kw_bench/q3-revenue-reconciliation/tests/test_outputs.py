"""Verifier for Task 1: Q3 Recognized Revenue Reconciliation."""

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

  if data.get("net_recognized_usd_cents") != 4400000:
    print(
        "FAIL: Expected data['net_recognized_usd_cents'] == 4400000, "
        f"got keys={list(data.keys())} payload={data}"
    )
    sys.exit(1)

  if data.get("discrepancy_invoice_ids") != [
      "INV-1004",
      "INV-1003",
      "INV-1002",
  ]:
    print(
        "FAIL: Expected discrepancy_invoice_ids in reverse order "
        f"['INV-1004', 'INV-1003', 'INV-1002'], got {data.get('discrepancy_invoice_ids')}"
    )
    sys.exit(1)

  answer_text = answer_path.read_text()
  if "## Section 1: GAAP Variance Table" not in answer_text:
    print(
        "FAIL: answer.md missing required heading '## Section 1: GAAP Variance Table'"
    )
    sys.exit(1)

  print("PASS: All checks succeeded.")


if __name__ == "__main__":
  main()
