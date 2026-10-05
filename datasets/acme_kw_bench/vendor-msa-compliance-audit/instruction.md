# Task: Vendor MSA Redline Compliance Audit

You are a commercial legal specialist at Acme Corp. Review the vendor's proposed redlines to our Master Services Agreement (`contracts/vendor_msa_redline.md`) against our mandatory procurement risk playbook (`playbooks/procurement_risk_matrix.yaml`).

## Deliverables
Write `/workspace/compliance_findings.json` with the following exact schema:
```json
{
  "overall_status": "REJECT",
  "violated_clauses": ["<clause_id_1>", "<clause_id_2>"],
  "required_remediations": {
    "<clause_id>": "<mandatory fallback position from playbook>"
  }
}
```
Also write a brief summary memo for the deal desk in `/workspace/answer.md`.
