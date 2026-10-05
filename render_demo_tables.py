#!/usr/bin/env python3
"""Renders formatted terminal tables from the pre-baked Harbor artifacts.

Run this script to view the reference tables from the presentation:
  python3 render_demo_tables.py
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent / "prebaked_artifacts"


def print_banner(title: str) -> None:
  print("\n" + "=" * 98)
  print(f"  {title}")
  print("=" * 98)


def main() -> None:
  # 1. harbor check report
  check_data = json.loads((BASE_DIR / "check_report_v1_flawed.json").read_text())
  print_banner("STAGE 2: `harbor check datasets/acme_kw_bench -r rubrics/bias_and_spec_check.toml`")
  print(
      f"{'Task Name':<30} | {'Spec in Prompt':<16} | {'Unbiased Prose':<16} | "
      f"{'Hermetic Test':<15} | {'Path Alignment':<15}"
  )
  print("-" * 98)
  for r in check_data["results"]:
    c = r["checks"]
    fmt = lambda k: "✅ PASS" if c[k]["outcome"] == "pass" else "❌ FAIL"
    print(
        f"{r['task_name']:<30} | {fmt('behavior_in_task_description'):<15} | "
        f"{fmt('unbiased_prose_grading'):<15} | {fmt('hermetic_verifier_execution'):<14} | "
        f"{fmt('workdir_and_path_alignment'):<14}"
    )

  # 2. harbor analyze report
  analyze_data = json.loads(
      (BASE_DIR / "analysis_exp1_customer_baseline.json").read_text()
  )
  print_banner(
      "STAGE 3: `harbor analyze jobs/exp1_customer_baseline --failing -r rubrics/harness_defect_analysis.toml`"
  )
  print(
      f"{'Trial Name':<48} | {'Stderr Visible':<15} | {'Turn-Cap Safe':<15} | {'Spec Aligned':<14}"
  )
  print("-" * 98)
  for r in analyze_data["results"]:
    c = r["checks"]
    fmt = lambda k: "✅ PASS" if c[k]["outcome"] == "pass" else "❌ FAIL"
    print(
        f"{r['trial_name']:<48} | {fmt('tool_error_visibility'):<14} | "
        f"{fmt('turn_cap_commit_discipline'):<14} | {fmt('task_specification_alignment'):<13}"
    )

  # 3. Experiment Scorecard
  scorecard = json.loads((BASE_DIR / "experiment_scorecard.json").read_text())
  print_banner(f"FINAL SCORECARD: {scorecard['benchmark']}")
  print(
      f"{'Experiment':<28} | {'Setup & Configuration':<32} | {'Pass@1':<8} | "
      f"{'Pass^3':<8} | {'Steps':<6} | {'$/Solved':<8}"
  )
  print("-" * 98)
  for exp in scorecard["experiments"]:
    cost_s = (
        f"${exp['avg_cost_per_resolved_usd']:.2f}"
        if exp["avg_cost_per_resolved_usd"] is not None
        else "  —   "
    )
    print(
        f"{exp['name']:<28} | {exp['harness'][:32]:<32} | "
        f"{exp['pass_at_1_pct']:>6.1f}% | {exp['pass_pow_3_pct']:>6.1f}% | "
        f"{exp['avg_steps']:>6.1f} | {cost_s:>8}"
    )
  print()


if __name__ == "__main__":
  main()
