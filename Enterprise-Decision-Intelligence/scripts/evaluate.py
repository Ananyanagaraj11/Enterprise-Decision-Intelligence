#!/usr/bin/env python3
"""Evaluation vs proposal baselines (detection, RCA, utility, latency)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from enterprise_decision_intel.data_pipeline import load_ga4_style_csv
from enterprise_decision_intel.evaluation.runner import (
    conflict_reeval_smoke_test,
    evaluation_table,
    run_advanced_evaluation,
    run_evaluation_csv,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Evaluate agentic system vs baselines")
    p.add_argument("--csv", required=True, help="GA4 daily CSV (e.g. data/ga4_public_daily.csv)")
    p.add_argument(
        "--mode",
        choices=("inject", "oracle"),
        default="inject",
        help="inject: controlled spikes + RCA labels; oracle: strict z labels only (no RCA GT)",
    )
    p.add_argument("--inject-events", type=int, default=10, help="Number of injected anomalies (inject mode)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--metric", default="revenue")
    p.add_argument("--runs", type=int, default=3, help="Advanced evaluation multi-run count (3-5)")
    p.add_argument("--advanced", action="store_true", help="Run multi-run + t-test + optional kappa")
    p.add_argument("--check-reeval", action="store_true", help="Run conflict-triggered re-evaluation smoke test")
    p.add_argument("--out", type=Path, help="Write JSON report to this path")
    args = p.parse_args()

    report = run_evaluation_csv(
        args.csv,
        mode=args.mode,
        inject_events=args.inject_events,
        seed=args.seed,
        metric_col=args.metric,
    )
    table = evaluation_table(report)
    report["comparison_table"] = table.to_dict(orient="records")
    if args.advanced:
        df = load_ga4_style_csv(args.csv)
        report["advanced"] = run_advanced_evaluation(df, metric_col=args.metric, runs=args.runs, base_seed=args.seed)
    if args.check_reeval:
        df = load_ga4_style_csv(args.csv)
        report["reeval_smoke_test"] = conflict_reeval_smoke_test(df, metric_col=args.metric)
    text = json.dumps(report, indent=2)
    print(text)
    print("\n=== Comparison Table ===")
    print(table.to_string(index=False))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"\nWrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
