#!/bin/bash
set -euo pipefail

cat <<'EOF' > /workspace/compliance_findings.json
{
  "overall_status": "REJECT",
  "violated_clauses": ["SEC-8.1", "SEC-11.3", "SEC-14.1"],
  "required_remediations": {
    "SEC-8.1": "Restore cap to 2.0x annual fees.",
    "SEC-11.3": "Remove non-US/EU regions (ap-southeast-1 prohibited).",
    "SEC-14.1": "Reduce notice period to 30 days."
  }
}
EOF

cat <<'EOF' > /workspace/answer.md
# Deal Desk Compliance Audit Summary
**Status**: REJECT (3 policy violations identified)
- **SEC-8.1 (Limitation of Liability)**: Proposed 0.5x cap violates the 2.0x minimum.
- **SEC-11.3 (Data Residency)**: Includes `ap-southeast-1`, violating US/EU-only policy.
- **SEC-14.1 (Termination Notice)**: Proposed 90-day notice exceeds the 30-day maximum.
EOF
