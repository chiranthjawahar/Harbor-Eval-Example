# Running Fair Agent Evaluations with Harbor — Hands-On Debugging Lab

Welcome to the hands-on debugging lab for **Running Fair Agent Evaluations with Harbor**.

In this lab, you will investigate a realistic customer benchmark where **Gemini 3.1 Pro** initially scored **0.0% (0/3)** against an existing model's **66.7% (2/3)**—and discover why **100% of the gap was caused by grader bias, broken test scripts, and agent harness defects** rather than model capability.

---

## 🎯 Lab Scenario

Acme Corp built a 3-task **Enterprise Knowledge-Work Benchmark** (`datasets/acme_kw_bench/`) and a custom Python agent harness (`harnesses/acme_agent.py`):

| Task Directory | Domain | Task Objective | Initial Score (Old Model) | Initial Score (Gemini 3.1 Pro) |
| :--- | :--- | :--- | :---: | :---: |
| `q3-revenue-reconciliation` | **Finance** | Reconcile payment exports (`stripe_exports.csv`) against the ERP ledger (`erp_ledger.json`) using `accounting_policy.md`. | **1.0** | **0.0** |
| `vendor-msa-compliance-audit` | **Legal** | Audit a redlined vendor MSA (`vendor_msa_redline.md`) against `procurement_risk_matrix.yaml`. | **0.0** | **0.0** |
| `customer-escalation-rca` | **Support** | Query `support_tickets.db` (SQLite) and correlate enterprise SLA breaches with incident postmortems (`INC-402.md`, `INC-409.md`). | **1.0** | **0.0** |

Your goal is to use the **4-Stage Harbor Diagnostic Workflow** to find and fix every flaw in `datasets/acme_kw_bench/` and `harnesses/acme_agent.py` until `python3 verify_lab.py` passes **3/3 Stages (100%)**.

---

## 🚀 Quick Start

### 1. Run the Interactive Lab Verifier

You can test the benchmark and your fixes at any time using the zero-dependency local verifier (`verify_lab.py`), which simulates the air-gapped task containers and audits both the task graders and the agent harness:

```bash
python3 verify_lab.py
```

On the `main` branch (the unmodified customer submission), all 3 stages start in a **FAIL** state:
- `python3 verify_lab.py --stage 1` — Runs the `nop` (do-nothing) and `oracle` (reference solution) sanity bounds.
- `python3 verify_lab.py --stage 2` — Audits the 3 task specifications and grader scripts (`harbor check`).
- `python3 verify_lab.py --stage 3` — Audits the customer agent harness (`harnesses/acme_agent.py`).

### 2. View Pre-Baked Reference Tables (Optional)

To print the formatted terminal tables from the presentation walkthrough (`harbor check`, `harbor analyze`, and the 7-step Experiment Scorecard):

```bash
python3 render_demo_tables.py
```

---

## 🔍 Step-by-Step Debugging Guide

### Stage 1: Verify Sanity Bounds (`nop` & `oracle`)

Before spending a single token on LLM calls, verify that the benchmark's floor (`nop`) is `0.0` and ceiling (`oracle`) is `1.0`.

Run the Stage 1 check locally (or via `harbor run -c configs/exp0_sanity_bounds.yaml`):

```bash
python3 verify_lab.py --stage 1
```

**What to look for:**
- Why does `vendor-msa-compliance-audit` score **`0`** even when running the reference answer key (`solution/solve.sh`)?
- Open `datasets/acme_kw_bench/vendor-msa-compliance-audit/tests/test.sh` and compare it against `datasets/acme_kw_bench/vendor-msa-compliance-audit/instruction.md` and `solution/solve.sh`.

<details>
<summary>💡 <b>Hint: How to fix Stage 1 (Task 2 Verifier Bug)</b></summary>

In `datasets/acme_kw_bench/vendor-msa-compliance-audit/tests/test.sh`:
1. **Air-Gapped Network Call**: `test.sh` runs `pip install pyyaml` at test time, which fails because the verifier container runs with internet disabled (`allow_internet = false`)—and `pyyaml` isn't even used by the Python test script! Remove the `pip install pyyaml` line.
2. **Wrong File Path**: `test.sh` checks `/app/compliance_findings.json`, whereas `WORKDIR` and `instruction.md` specify `/workspace/compliance_findings.json`. Change `/app/compliance_findings.json` to `/workspace/compliance_findings.json`.
</details>

---

### Stage 2: Audit for Grader & Specification Bias (`harbor check`)

Next, check whether the task instructions (`instruction.md`) fairly specify everything the grader scripts (`tests/`) assert.

Run the Stage 2 audit locally (or via `harbor check datasets/acme_kw_bench -m vertex_ai/gemini-3.1-pro-preview -r rubrics/bias_and_spec_check.toml`):

```bash
python3 verify_lab.py --stage 2
```

**What to look for:**
- Inspect `datasets/acme_kw_bench/q3-revenue-reconciliation/instruction.md` and `datasets/acme_kw_bench/q3-revenue-reconciliation/tests/test_outputs.py`.
- Why did Gemini 3.1 Pro calculate the exact right Q3 revenue (`$44,000.00`) and the exact right 3 discrepancy invoices (`INV-1002`, `INV-1003`, `INV-1004`), yet still get a `0.0` from `test_outputs.py`?

<details>
<summary>💡 <b>Hint: How to fix Stage 2 (Task 1 Grader & Prompt Bias)</b></summary>

In `datasets/acme_kw_bench/q3-revenue-reconciliation/`:
1. **Document the JSON Schema in `instruction.md`**: Update `instruction.md` so the required JSON keys (`recognized_revenue_usd` in USD dollars and `discrepancy_invoice_ids` as a list of invoice ID strings) are explicitly documented in the prompt (without leaking the literal answer numbers `44000` in `instruction.md`).
2. **Fix Biased Assertions in `tests/test_outputs.py`**:
   - Check `recognized_revenue_usd` (`44000.0`) instead of the undocumented `net_recognized_usd_cents` (`4400000`).
   - Compare `set(data.get("discrepancy_invoice_ids", [])) == {"INV-1002", "INV-1003", "INV-1004"}` so any list order is accepted.
   - Remove the hardcoded check for the old model's markdown heading (`## Section 1: GAAP Variance Table`) and instead check that `answer.md` mentions each discrepancy invoice ID (`INV-1002`, `INV-1003`, `INV-1004`).
</details>

---

### Stage 3: Triage Agent Harness Defects (`harbor analyze`)

Once Stages 1 and 2 pass, Task 1 and Task 2 are fair—but Gemini still fails or times out intermittently on Task 3 (`customer-escalation-rca`) when using the customer's custom harness (`harnesses/acme_agent.py`), even though it scores **100%** on Harbor's built-in reference harness (`antigravity-sdk`).

Compare the failing and fixed trajectories in `prebaked_artifacts/trajectory_task3_legacy_defect.json` vs. `prebaked_artifacts/trajectory_task3_fixed_agent.json`, then run Stage 3:

```bash
python3 verify_lab.py --stage 3
```

**What to look for in `harnesses/acme_agent.py`:**
1. What happens in `acme_agent.py` when `exec_res.return_code != 0`? Does the model ever see `exec_res.stderr`?
2. How are tools invoked, and how is the model's response appended to `history`? Are Gemini 3 `thought_signature` parts preserved across turns?
3. What `thinking_level` and `max_output_tokens` are passed in `GenerateContentConfig`?
4. What happens when `max_turns = 8` is reached before `/workspace/answer.md` is written?

<details>
<summary>💡 <b>Hint: How to fix Stage 3 (`harnesses/acme_agent.py`)</b></summary>

Update `harnesses/acme_agent.py` to fix all 4 harness defects:
1. **Return `stderr` on Non-Zero Exit Codes**: Include `exec_res.stderr` in the tool response so the model can see SQL/Python error messages and self-correct in 1 turn.
2. **Use Native Function Calling & Preserve `thought_signature`**: Declare structured tools (`types.FunctionDeclaration` for `run_bash` and `finish_task`) and append `response.candidates[0].content` directly to `history` instead of regex-parsing `<bash>` tags from `response.text`.
3. **Match Gemini 3 Thinking Effort**: Set `thinking_config=types.ThinkingConfig(thinking_level="HIGH")` and `max_output_tokens=8192` on `genai.Client(vertexai=True)` with `gemini-3.1-pro-preview` (and do not set `temperature`).
4. **Raise Turn Cap & Add Pre-Cutoff Warning**: Increase `max_turns = 20` and inject a warning when `turn == max_turns - 1` reminding the agent to write `/workspace/answer.md` and call `finish_task`.
</details>

---

## ✅ Checking the Reference Solution (`solution` branch)

At any time, you can compare your work against the reference `solution` branch using `git diff`:

```bash
# View all fixes across the benchmark and harness
git diff main..solution

# View only the agent harness fixes
git diff main..solution -- harnesses/acme_agent.py

# Switch to the solution branch and verify all 3 stages pass
git checkout solution
python3 verify_lab.py
```
