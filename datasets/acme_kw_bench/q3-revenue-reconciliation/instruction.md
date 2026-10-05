# Task: Q3 Recognized Revenue Reconciliation

You are a financial operations analyst at Acme Corp. Close of Q3 is tomorrow, and the VP of Finance needs you to reconcile our payment processor exports against the ERP general ledger according to our internal revenue recognition policy.

## Input Files in `/workspace`
1. `data/stripe_exports.csv` — Raw Q3 payment processor charges and statuses.
2. `data/erp_ledger.json` — Recorded Q3 invoice entries in the ERP system.
3. `docs/accounting_policy.md` — Acme's official Q3 revenue recognition rules (covering FX conversion rates, refunded charges, and annual contract proration).

## Deliverables
1. **`/workspace/reconciliation_report.json`**: A JSON file summarizing the Q3 recognized revenue in USD and listing any invoices that have a discrepancy between Stripe and the ERP ledger.
2. **`/workspace/answer.md`**: A concise executive summary explaining the total recognized Q3 revenue and the root cause of each discrepancy found.
