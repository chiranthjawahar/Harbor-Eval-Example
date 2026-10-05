#!/usr/bin/env python3
"""Interactive Self-Check & Sandbox Verifier for the Harbor Evaluation Lab.

Run this script at any point while debugging the benchmark and agent harness:
  python3 verify_lab.py
  python3 verify_lab.py --stage 1   # Run Stage 1 (nop & oracle sanity bounds)
  python3 verify_lab.py --stage 2   # Run Stage 2 (Dataset & Grader Bias Audit)
  python3 verify_lab.py --stage 3   # Run Stage 3 (Agent Harness Defect Audit)
"""

import argparse
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BENCH_DIR = ROOT_DIR / "datasets" / "acme_kw_bench"
HARNESS_PATH = ROOT_DIR / "harnesses" / "acme_agent.py"

TASKS = [
    "q3-revenue-reconciliation",
    "vendor-msa-compliance-audit",
    "customer-escalation-rca",
]


def banner(title: str) -> None:
  print("\n" + "=" * 92)
  print(f"  {title}")
  print("=" * 92)


def _prepare_sandbox(task_dir: Path, sandbox: Path) -> None:
  """Prepares a local directory simulating the task container filesystem."""
  ws = sandbox / "workspace"
  tests = sandbox / "tests"
  logs = sandbox / "logs" / "verifier"
  app = sandbox / "app"
  ws.mkdir(parents=True, exist_ok=True)
  tests.mkdir(parents=True, exist_ok=True)
  logs.mkdir(parents=True, exist_ok=True)
  app.mkdir(parents=True, exist_ok=True)

  env_dir = task_dir / "environment"
  for item in env_dir.iterdir():
    if item.name == "Dockerfile":
      continue
    dest = ws / item.name
    if item.is_dir():
      shutil.copytree(item, dest, dirs_exist_ok=True)
    else:
      shutil.copy2(item, dest)

  # Initialize SQLite DB if seed_support.sql is present (Task 3)
  seed_sql = ws / "data" / "seed_support.sql"
  if seed_sql.exists():
    db_path = ws / "data" / "support_tickets.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(seed_sql.read_text())
    conn.close()

  # Copy and rewrite paths in tests/
  for item in (task_dir / "tests").iterdir():
    content = item.read_text()
    content = (
        content.replace("/workspace", str(ws))
        .replace("/tests", str(tests))
        .replace("/logs", str(sandbox / "logs"))
        .replace("/app", str(app))
    )
    # Simulate air-gapped verifier container (allow_internet = false)
    content = re.sub(
        r"^\s*pip3?\s+install\b.*$",
        'echo "ERROR: Network is disabled in verifier container (allow_internet=false)" >&2; false',
        content,
        flags=re.MULTILINE,
    )
    out_file = tests / item.name
    out_file.write_text(content)
    out_file.chmod(0o755)


def _run_trial_in_sandbox(task_dir: Path, run_oracle: bool) -> tuple[int, str]:
  """Runs nop or oracle in a temporary container sandbox and returns (reward, log)."""
  with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    _prepare_sandbox(task_dir, sandbox)
    ws = sandbox / "workspace"

    if run_oracle:
      solve_txt = (task_dir / "solution" / "solve.sh").read_text()
      solve_txt = solve_txt.replace("/workspace", str(ws)).replace(
          "/app", str(sandbox / "app")
      )
      solve_script = sandbox / "solve.sh"
      solve_script.write_text(solve_txt)
      solve_script.chmod(0o755)
      subprocess.run(
          ["bash", str(solve_script)],
          cwd=str(ws),
          capture_output=True,
          text=True,
          check=False,
      )

    test_script = sandbox / "tests" / "test.sh"
    subprocess.run(
        ["bash", str(test_script)],
        cwd=str(ws),
        capture_output=True,
        text=True,
        check=False,
    )
    reward_file = sandbox / "logs" / "verifier" / "reward.txt"
    stdout_file = sandbox / "logs" / "verifier" / "test-stdout.txt"
    reward = (
        int(reward_file.read_text().strip())
        if reward_file.exists() and reward_file.read_text().strip().isdigit()
        else 0
    )
    log_text = stdout_file.read_text().strip() if stdout_file.exists() else ""
    log_text = log_text.replace(str(sandbox), "")
    return reward, log_text


def check_stage1() -> bool:
  banner("STAGE 1: Sanity Bounds (`nop` & `oracle` Answer-Key Verification)")
  print(f"{'Task':<32} | {'nop (Target: 0)':<17} | {'oracle (Target: 1)':<20} | {'Status'}")
  print("-" * 92)
  all_ok = True
  failures: list[tuple[str, str]] = []

  for task_name in TASKS:
    task_dir = BENCH_DIR / task_name
    nop_reward, _ = _run_trial_in_sandbox(task_dir, run_oracle=False)
    oracle_reward, oracle_log = _run_trial_in_sandbox(task_dir, run_oracle=True)
    ok = (nop_reward == 0) and (oracle_reward == 1)
    if not ok:
      all_ok = False
      failures.append((task_name, oracle_log))
    status = "✅ PASS" if ok else "❌ FAIL"
    print(f"{task_name:<32} | {nop_reward:<17} | {oracle_reward:<20} | {status}")

  if failures:
    print("\n[Stage 1 Diagnostic Details]")
    for task_name, log_text in failures:
      first_line = log_text.splitlines()[0] if log_text else "Verifier exited with reward 0"
      print(f"  • {task_name}: {first_line}")
      print(f"    -> Inspect: datasets/acme_kw_bench/{task_name}/tests/test.sh")
  return all_ok


def check_stage2() -> bool:
  banner("STAGE 2: Dataset & Grader Bias Audit (`harbor check`)")
  print(
      f"{'Task':<30} | {'Spec in Prompt':<15} | {'Unbiased Prose':<15} | "
      f"{'Hermetic Test':<14} | {'Path Aligned'}"
  )
  print("-" * 92)

  all_ok = True
  findings: list[str] = []

  for task_name in TASKS:
    task_dir = BENCH_DIR / task_name
    instr = (task_dir / "instruction.md").read_text()
    test_sh = (task_dir / "tests" / "test.sh").read_text()
    test_py_path = task_dir / "tests" / "test_outputs.py"
    test_code = test_sh + ("\n" + test_py_path.read_text() if test_py_path.exists() else "")

    # Check 1: Spec in prompt (no undocumented keys or reverse-order traps, and no leaked answer values)
    spec_ok = True
    if "net_recognized_usd_cents" in test_code and "net_recognized_usd_cents" not in instr:
      spec_ok = False
      findings.append(
          f"{task_name}: Grader asserts undocumented key `net_recognized_usd_cents` not in instruction.md."
      )
    if '["INV-1004", "INV-1003", "INV-1002"]' in test_code or "INV-1004',\n      'INV-1003'" in test_code:
      spec_ok = False
      findings.append(
          f"{task_name}: Grader enforces undocumented reverse list order on `discrepancy_invoice_ids`."
      )
    if task_name == "q3-revenue-reconciliation" and "recognized_revenue_usd" not in instr:
      spec_ok = False
      findings.append(
          f"{task_name}: `instruction.md` does not document the expected JSON keys (`recognized_revenue_usd`, `discrepancy_invoice_ids`)."
      )
    if task_name == "q3-revenue-reconciliation" and ("44000" in instr or "44,000" in instr):
      spec_ok = False
      findings.append(
          f"{task_name}: `instruction.md` leaks the ground-truth answer (`44000`) inside the prompt!"
      )

    # Check 2: Unbiased prose grading
    prose_ok = "## Section 1: GAAP Variance Table" not in test_code
    if not prose_ok:
      findings.append(
          f"{task_name}: Grader requires undocumented prose heading `## Section 1: GAAP Variance Table`."
      )

    # Check 3: Hermetic verifier execution
    hermetic_ok = not bool(re.search(r"^\s*pip3?\s+install\b", test_sh, flags=re.MULTILINE))
    if not hermetic_ok:
      findings.append(
          f"{task_name}: `tests/test.sh` runs `pip install` in an air-gapped verifier container."
      )

    # Check 4: Workdir & path alignment
    path_ok = "/app/" not in test_code
    if not path_ok:
      findings.append(
          f"{task_name}: Grader checks `/app/...` instead of `/workspace/...`."
      )

    row_ok = spec_ok and prose_ok and hermetic_ok and path_ok
    if not row_ok:
      all_ok = False

    fmt = lambda ok: "✅ PASS" if ok else "❌ FAIL"
    print(
        f"{task_name:<30} | {fmt(spec_ok):<14} | {fmt(prose_ok):<14} | "
        f"{fmt(hermetic_ok):<13} | {fmt(path_ok)}"
    )

  if findings:
    print("\n[Stage 2 Audit Findings]")
    for f in findings:
      print(f"  • {f}")
  return all_ok


def check_stage3() -> bool:
  banner("STAGE 3: Agent Harness Defect Audit (`harnesses/acme_agent.py`)")
  code = HARNESS_PATH.read_text()

  checks = {
      "1. Tool Error Visibility (returns `exec_res.stderr` on error)": (
          "exec_res.stderr" in code
      ),
      "2. Native Tool Calling & Preserved `thought_signature` (`candidate.content`)": (
          "FunctionDeclaration" in code
          and "candidates[0].content" in code
          and "<bash>" not in code
      ),
      "3. Matched Gemini 3 Config (`thinking_level=\"HIGH\"`, no hardcoded temperature)": (
          'thinking_level="HIGH"' in code
          and "temperature=" not in code
      ),
      "4. Turn-Cap Protection (`max_turns >= 15` + pre-cutoff commit warning)": (
          bool(re.search(r"max_turns\s*=\s*(1[5-9]|[2-9]\d)", code))
          and ("max_turns - 1" in code or "turns remaining" in code.lower())
      ),
  }

  all_ok = True
  for label, ok in checks.items():
    if not ok:
      all_ok = False
    status = "✅ PASS" if ok else "❌ FAIL"
    print(f"  {status}  {label}")

  if not all_ok:
    print(
        "\n  -> Edit `harnesses/acme_agent.py` to fix the failing harness checks above."
    )
  return all_ok


def main() -> None:
  parser = argparse.ArgumentParser(description="Verify Harbor Evaluation Lab progress.")
  parser.add_argument(
      "--stage",
      type=int,
      choices=[1, 2, 3],
      help="Run only a specific diagnostic stage (1, 2, or 3).",
  )
  args = parser.parse_args()

  if args.stage == 1:
    sys.exit(0 if check_stage1() else 1)
  if args.stage == 2:
    sys.exit(0 if check_stage2() else 1)
  if args.stage == 3:
    sys.exit(0 if check_stage3() else 1)

  s1 = check_stage1()
  s2 = check_stage2()
  s3 = check_stage3()

  banner("OVERALL LAB SCORECARD")
  passed = sum([s1, s2, s3])
  print(f"  • Stage 1 (Sanity Bounds: `nop`=0, `oracle`=1): {'✅ PASS' if s1 else '❌ FAIL'}")
  print(f"  • Stage 2 (Dataset & Grader Bias Audit):        {'✅ PASS' if s2 else '❌ FAIL'}")
  print(f"  • Stage 3 (Agent Harness Defect Audit):         {'✅ PASS' if s3 else '❌ FAIL'}")
  print("-" * 92)
  if passed == 3:
    print("  🎉 ALL STAGES PASSED (3/3)! The benchmark and agent harness are ready for a fair evaluation.")
    sys.exit(0)
  else:
    print(
        f"  🔧 {passed}/3 stages passing. Follow the steps in README.md to diagnose and fix the remaining defects!"
    )
    sys.exit(1)


if __name__ == "__main__":
  main()
