# Task: Enterprise SLA Breach Root-Cause Analysis (RCA)

You are the Staff Operations Analyst preparing for the weekly Reliability Review. Query the support ticket database (`/workspace/data/support_tickets.db`) and cross-reference the linked engineering postmortems in `/workspace/postmortems/` to quantify Enterprise ARR at risk from Q3 SLA breaches.

## Rules
1. An **Enterprise SLA Breach** occurs when a customer with `tier = 'enterprise'` experiences a first-response latency strictly greater than **60 minutes**.
2. Map each breached ticket's `linked_incident_id` to its postmortem markdown file in `/workspace/postmortems/` to identify the `owning_team` and `remediation_eta`.

## Deliverables
1. **`/workspace/sla_breach_rca.json`**:
   ```json
   {
     "breached_ticket_ids": ["TKT-901", "TKT-904"],
     "total_enterprise_arr_at_risk_usd": 1450000,
     "by_owning_team": {
       "Auth-Platform": {
         "arr_at_risk_usd": 1450000,
         "incident_id": "INC-402",
         "remediation_eta": "2026-10-15"
       }
     }
   }
   ```
2. **`/workspace/answer.md`**: Executive brief summarizing the breached enterprise accounts, root cause from the postmortem, and remediation ETA.
