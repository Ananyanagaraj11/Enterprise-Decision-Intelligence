#!/usr/bin/env python3
"""Run the agentic pipeline on a CSV produced from the public GA4 BigQuery sample."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from enterprise_decision_intel.config import detection_sensitivity
from enterprise_decision_intel.pipeline import last_anomaly_report, run_dataset


def main() -> None:
    p = argparse.ArgumentParser(description="Enterprise decision intelligence (agentic pipeline)")
    p.add_argument(
        "--csv",
        required=True,
        help="CSV from scripts/fetch_ga4_bigquery.py (public GA4 sample, no bundled fake data)",
    )
    p.add_argument("--metric", default="revenue", help="Metric column to monitor")
    p.add_argument(
        "--approve",
        action="store_true",
        help="Simulate human approval so execution_status can become approved_for_execution",
    )
    p.add_argument(
        "--sensitivity",
        choices=("standard", "balanced", "sensitive", "explorer"),
        default="standard",
        help="Same real CSV: lower z-threshold → more anomaly days (no injection). Evaluation scripts keep standard.",
    )
    p.add_argument("--json", action="store_true", help="Print full JSONL for all days")
    args = p.parse_args()
    path = Path(args.csv)
    if not path.is_file():
        print(
            f"File not found: {path}\n"
            "Export real data first (BigQuery free tier):\n"
            "  gcloud auth application-default login\n"
            "  pip install -r requirements_fetch.txt\n"
            "  python scripts/fetch_ga4_bigquery.py --out data/ga4_public_daily.csv\n"
            "  python scripts/fetch_thelook_bigquery.py --out data/thelook_ecommerce_daily.csv",
            file=sys.stderr,
        )
        sys.exit(1)
    det = detection_sensitivity(args.sensitivity)
    result = run_dataset(
        path,
        metric_col=args.metric,
        human_approved=args.approve,
        detection=det,
    )
    if args.json:
        for row in result.rows:
            print(json.dumps(row, default=str))
        return
    hit = last_anomaly_report(result.rows)
    row = hit or result.rows[-1]
    print(f"Date: {row.get('date')}")
    print(f"Metric: {row.get('metric_name')}")
    print(f"Anomaly detected: {row.get('is_anomaly')} (score={row.get('anomaly_score')}, confidence={row.get('confidence')})")
    if row.get("root_causes_ranked"):
        print("Root causes:")
        for rc in row["root_causes_ranked"][:5]:
            print(f"  - {rc['dimension']}={rc['value']}: {rc['contribution_pct']}%")
    if row.get("ranked_actions"):
        print("Ranked actions:")
        for a in row["ranked_actions"][:3]:
            print(f"  - {a['label']} (utility={a['utility']})")
    print(f"Execution status: {row.get('execution_status')}")
    print("\nExplanation:")
    print(row.get("explanation_text", ""))


if __name__ == "__main__":
    main()
