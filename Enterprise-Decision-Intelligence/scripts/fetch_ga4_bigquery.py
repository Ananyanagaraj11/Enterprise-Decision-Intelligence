#!/usr/bin/env python3
"""
Pull daily aggregates from the official BigQuery public dataset:
  bigquery-public-data.ga4_obfuscated_sample_ecommerce

Uses the BigQuery free monthly query allowance (no synthetic CSV in-repo).
For a longer, richer e-commerce series see scripts/fetch_thelook_bigquery.py (The Look public dataset).
Requires: gcloud auth application-default login  OR  GOOGLE_APPLICATION_CREDENTIALS
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    from google.cloud import bigquery
except ImportError:
    print("Install fetch deps: pip install -r requirements_fetch.txt", file=sys.stderr)
    sys.exit(1)

import pandas as pd

PROJECT_TABLE = "`bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`"


def _slug(s: str, prefix: str) -> str:
    t = re.sub(r"[^a-zA-Z0-9]+", "_", str(s).strip() or "unknown").strip("_")
    return f"{prefix}{t[:48]}"


def main() -> None:
    p = argparse.ArgumentParser(description="Export GA4 public sample to CSV for the agentic pipeline")
    p.add_argument("--out", type=Path, default=ROOT / "data" / "ga4_public_daily.csv")
    p.add_argument("--max-countries", type=int, default=8)
    p.add_argument("--max-mediums", type=int, default=6)
    p.add_argument(
        "--project",
        default=os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT"),
        help="GCP project ID for query quota (same as gcloud auth application-default set-quota-project)",
    )
    p.add_argument(
        "--suffix-start",
        default="20201101",
        help="Inclusive _TABLE_SUFFIX lower bound (YYYYMMDD). Public sample is mostly Nov 2020–Jan 2021.",
    )
    p.add_argument(
        "--suffix-end",
        default="20210131",
        help="Inclusive _TABLE_SUFFIX upper bound. Wider range = more daily rows if partitions exist.",
    )
    args = p.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    suffix_range = f"BETWEEN '{args.suffix_start}' AND '{args.suffix_end}'"
    client = bigquery.Client(project=args.project) if args.project else bigquery.Client()

    q_daily = f"""
    SELECT
      PARSE_DATE('%Y%m%d', event_date) AS date,
      SUM(IFNULL(ecommerce.purchase_revenue_in_usd, 0)) AS revenue,
      COUNTIF(event_name = 'purchase') AS purchases,
      COUNTIF(event_name = 'session_start') AS sessions
    FROM {PROJECT_TABLE}
    WHERE _TABLE_SUFFIX {suffix_range}
    GROUP BY 1
    ORDER BY 1
    """

    q_country = f"""
    SELECT
      PARSE_DATE('%Y%m%d', event_date) AS date,
      IFNULL(geo.country, '(not set)') AS country,
      SUM(IFNULL(ecommerce.purchase_revenue_in_usd, 0)) AS rev
    FROM {PROJECT_TABLE}
    WHERE _TABLE_SUFFIX {suffix_range}
      AND event_name = 'purchase'
    GROUP BY 1, 2
    """

    q_medium = f"""
    SELECT
      PARSE_DATE('%Y%m%d', event_date) AS date,
      IFNULL(traffic_source.medium, '(not set)') AS medium,
      SUM(IFNULL(ecommerce.purchase_revenue_in_usd, 0)) AS rev
    FROM {PROJECT_TABLE}
    WHERE _TABLE_SUFFIX {suffix_range}
      AND event_name = 'purchase'
    GROUP BY 1, 2
    """

    daily = client.query(q_daily).to_dataframe()
    if daily.empty:
        print("No rows returned; check BigQuery auth and dataset access.", file=sys.stderr)
        sys.exit(1)

    country = client.query(q_country).to_dataframe()
    medium = client.query(q_medium).to_dataframe()

    top_c = (
        country.groupby("country")["rev"].sum().sort_values(ascending=False).head(args.max_countries).index.tolist()
    )
    top_m = (
        medium.groupby("medium")["rev"].sum().sort_values(ascending=False).head(args.max_mediums).index.tolist()
    )

    c_f = country[country["country"].isin(top_c)].copy()
    m_f = medium[medium["medium"].isin(top_m)].copy()

    out = daily.copy()
    if not c_f.empty:
        cp = c_f.pivot_table(index="date", columns="country", values="rev", aggfunc="sum").fillna(0.0)
        cp = cp.rename(columns={c: _slug(c, "rev_region_") for c in cp.columns}).reset_index()
        out = out.merge(cp, on="date", how="left")
    if not m_f.empty:
        mp = m_f.pivot_table(index="date", columns="medium", values="rev", aggfunc="sum").fillna(0.0)
        mp = mp.rename(columns={c: _slug(c, "rev_channel_") for c in mp.columns}).reset_index()
        out = out.merge(mp, on="date", how="left")
    out = out.sort_values("date").reset_index(drop=True)
    num_cols = [c for c in out.columns if c != "date"]
    out[num_cols] = out[num_cols].fillna(0.0)
    sess = out["sessions"].astype(float).replace(0.0, float("nan"))
    out["conversion_rate"] = (out["purchases"].astype(float) / sess).fillna(0.0).clip(lower=0.0, upper=1.0)

    out.to_csv(args.out, index=False)
    print(f"Wrote {args.out} ({len(out)} rows)")


if __name__ == "__main__":
    main()
