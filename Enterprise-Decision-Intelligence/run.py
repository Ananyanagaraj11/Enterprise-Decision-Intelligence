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

from enterprise_decision_intel.pipeline import last_anomaly_report, run_dataset


def main() -> None:
    p = argparse.ArgumentParser(description="Enterprise decision intelligence (agentic pipeline)")
    p.add_argument(
        "--csv",
        required=True,
        help="CSV from scripts/fetch_ga4_bigquery.py (public GA4 sample, no bundled fake data)",
    )
    p.add_argument("--metric", default="revenue", help="Metric column to monitor")
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
    result = run_dataset(path, metric_col=args.metric)
    if args.json:
        for row in result.rows:
            print(json.dumps(row, default=str))
        return
    hit = last_anomaly_report(result.rows)
    if hit:
        print(json.dumps(hit, indent=2, default=str))
    else:
        print(json.dumps(result.rows[-1], indent=2, default=str))


if __name__ == "__main__":
    main()
