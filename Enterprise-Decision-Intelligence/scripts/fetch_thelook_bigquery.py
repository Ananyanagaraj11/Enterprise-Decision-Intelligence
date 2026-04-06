#!/usr/bin/env python3
"""
Export daily e-commerce aggregates from BigQuery public dataset:
  bigquery-public-data.thelook_ecommerce

Richer than the GA4 obfuscated sample: longer history (years), more KPIs
(revenue, orders, line items, active buyers, AOV), and splits by country + product category.

Requires: pip install -r requirements_fetch.txt, gcloud auth application-default login
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

THELOOK = "`bigquery-public-data.thelook_ecommerce`"


def _slug(s: str, prefix: str) -> str:
    t = re.sub(r"[^a-zA-Z0-9]+", "_", str(s).strip() or "unknown").strip("_")
    return f"{prefix}{t[:48]}"


def main() -> None:
    p = argparse.ArgumentParser(description="Export The Look eCommerce public data to daily CSV")
    p.add_argument("--out", type=Path, default=ROOT / "data" / "thelook_ecommerce_daily.csv")
    p.add_argument("--max-countries", type=int, default=10)
    p.add_argument("--max-categories", type=int, default=8)
    p.add_argument(
        "--project",
        default=os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT"),
        help="GCP project ID for query quota",
    )
    args = p.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    client = bigquery.Client(project=args.project) if args.project else bigquery.Client()

    # Core daily KPIs (line-item grain; filter out cancelled/returned lines)
    q_daily = f"""
    SELECT
      DATE(o.created_at) AS date,
      SUM(oi.sale_price) AS revenue,
      COUNT(DISTINCT o.order_id) AS purchases,
      COUNT(DISTINCT o.user_id) AS active_users,
      COUNT(*) AS line_items
    FROM {THELOOK}.order_items oi
    JOIN {THELOOK}.orders o ON oi.order_id = o.order_id
    WHERE oi.status NOT IN ('Cancelled', 'Canceled', 'Returned')
    GROUP BY 1
    ORDER BY 1
    """

    q_country = f"""
    SELECT
      DATE(o.created_at) AS date,
      IFNULL(u.country, '(not set)') AS country,
      SUM(oi.sale_price) AS rev
    FROM {THELOOK}.order_items oi
    JOIN {THELOOK}.orders o ON oi.order_id = o.order_id
    LEFT JOIN {THELOOK}.users u ON o.user_id = u.id
    WHERE oi.status NOT IN ('Cancelled', 'Canceled', 'Returned')
    GROUP BY 1, 2
    """

    q_category = f"""
    SELECT
      DATE(o.created_at) AS date,
      IFNULL(COALESCE(NULLIF(TRIM(p.category), ''), NULLIF(TRIM(CAST(p.department AS STRING)), '')), '(not set)') AS category,
      SUM(oi.sale_price) AS rev
    FROM {THELOOK}.order_items oi
    JOIN {THELOOK}.orders o ON oi.order_id = o.order_id
    JOIN {THELOOK}.products p ON oi.product_id = p.id
    WHERE oi.status NOT IN ('Cancelled', 'Canceled', 'Returned')
    GROUP BY 1, 2
    """

    daily = client.query(q_daily).to_dataframe()
    if daily.empty:
        print("No rows returned; check BigQuery auth and dataset access.", file=sys.stderr)
        sys.exit(1)

    country = client.query(q_country).to_dataframe()
    category = client.query(q_category).to_dataframe()

    top_c = (
        country.groupby("country")["rev"].sum().sort_values(ascending=False).head(args.max_countries).index.tolist()
    )
    top_cat = (
        category.groupby("category")["rev"]
        .sum()
        .sort_values(ascending=False)
        .head(args.max_categories)
        .index.tolist()
    )

    c_f = country[country["country"].isin(top_c)].copy()
    cat_f = category[category["category"].isin(top_cat)].copy()

    out = daily.copy()
    if not c_f.empty:
        cp = c_f.pivot_table(index="date", columns="country", values="rev", aggfunc="sum").fillna(0.0)
        cp = cp.rename(columns={c: _slug(c, "rev_region_") for c in cp.columns}).reset_index()
        out = out.merge(cp, on="date", how="left")
    if not cat_f.empty:
        kp = cat_f.pivot_table(index="date", columns="category", values="rev", aggfunc="sum").fillna(0.0)
        kp = kp.rename(columns={c: _slug(c, "rev_channel_") for c in kp.columns}).reset_index()
        out = out.merge(kp, on="date", how="left")

    out = out.sort_values("date").reset_index(drop=True)
    num_cols = [c for c in out.columns if c != "date"]
    out[num_cols] = out[num_cols].fillna(0.0)

    rev = out["revenue"].astype(float)
    pur = out["purchases"].astype(float).replace(0.0, float("nan"))
    li = out["line_items"].astype(float).replace(0.0, float("nan"))
    out["aov"] = (rev / pur).fillna(0.0)
    # Funnel-style rate: orders per line-item activity (bounded, comparable day-to-day)
    out["conversion_rate"] = (out["purchases"].astype(float) / li).fillna(0.0).clip(lower=0.0, upper=1.0)
    # Sessions proxy for compatibility with GA4-style pipeline / injection
    out["sessions"] = out["line_items"].astype(float)

    out.to_csv(args.out, index=False)
    print(f"Wrote {args.out} ({len(out)} rows, columns: {list(out.columns)})")


if __name__ == "__main__":
    main()
