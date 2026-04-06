from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class MetricSeries:
    """Daily series for one KPI (GA4 aggregates: revenue, conversion, etc.)."""

    name: str
    dates: pd.DatetimeIndex
    values: pd.Series


def load_ga4_style_csv(path: str | Path) -> pd.DataFrame:
    """Daily CSV: date, revenue, core KPIs, optional rev_region_* / rev_channel_* splits (GA4 or The Look exports)."""
    p = Path(path)
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = _ensure_derived_metrics(df)
    return df


def _ensure_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """GA4 fetch scripts may omit columns The Look includes; derive when possible."""
    out = df.copy()
    if "conversion_rate" not in out.columns and "purchases" in out.columns and "sessions" in out.columns:
        s = pd.to_numeric(out["sessions"], errors="coerce").replace(0.0, np.nan)
        p = pd.to_numeric(out["purchases"], errors="coerce").fillna(0.0)
        out["conversion_rate"] = (p / s).fillna(0.0)
    if "aov" not in out.columns and "revenue" in out.columns and "purchases" in out.columns:
        r = pd.to_numeric(out["revenue"], errors="coerce").fillna(0.0)
        p = pd.to_numeric(out["purchases"], errors="coerce").replace(0.0, np.nan)
        out["aov"] = (r / p).fillna(0.0)
    if "churn" not in out.columns:
        # Prefer active_users; fallback to users/session proxy for GA4 exports that omit active_users.
        base = None
        if "active_users" in out.columns:
            base = pd.to_numeric(out["active_users"], errors="coerce")
        elif "users" in out.columns:
            base = pd.to_numeric(out["users"], errors="coerce")
        elif "sessions" in out.columns:
            base = pd.to_numeric(out["sessions"], errors="coerce")
        if base is not None:
            base = base.ffill().fillna(0.0)
            prev = base.shift(1).replace(0.0, np.nan)
            out["churn"] = ((prev - base).clip(lower=0.0) / prev).fillna(0.0)
        else:
            out["churn"] = 0.0
    if "cac" not in out.columns:
        # Proxy CAC as estimated acquisition spend / new customers.
        traffic = None
        if "sessions" in out.columns:
            traffic = pd.to_numeric(out["sessions"], errors="coerce").fillna(0.0)
        elif "users" in out.columns:
            traffic = pd.to_numeric(out["users"], errors="coerce").fillna(0.0)
        purchases = pd.to_numeric(out["purchases"], errors="coerce").replace(0.0, np.nan) if "purchases" in out.columns else None
        if traffic is not None and purchases is not None:
            out["cac"] = (0.05 * traffic / purchases).fillna(0.0)
        else:
            out["cac"] = 0.0
    out = _ensure_dimension_coverage(out)
    return out


def recompute_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recompute KPI columns that depend on revenue / sessions / purchases after row-level edits
    (e.g. controlled anomaly injection). Without this, cac/churn/conversion_rate can stay stale.
    """
    out = df.copy()
    if "purchases" in out.columns and "sessions" in out.columns:
        s = pd.to_numeric(out["sessions"], errors="coerce").replace(0.0, np.nan)
        p = pd.to_numeric(out["purchases"], errors="coerce").fillna(0.0)
        out["conversion_rate"] = (p / s).fillna(0.0)
    if "revenue" in out.columns and "purchases" in out.columns:
        r = pd.to_numeric(out["revenue"], errors="coerce").fillna(0.0)
        p2 = pd.to_numeric(out["purchases"], errors="coerce").replace(0.0, np.nan)
        out["aov"] = (r / p2).fillna(0.0)
    base = None
    if "active_users" in out.columns:
        base = pd.to_numeric(out["active_users"], errors="coerce")
    elif "users" in out.columns:
        base = pd.to_numeric(out["users"], errors="coerce")
    elif "sessions" in out.columns:
        base = pd.to_numeric(out["sessions"], errors="coerce")
    if base is not None:
        base = base.ffill().fillna(0.0)
        prev = base.shift(1).replace(0.0, np.nan)
        out["churn"] = ((prev - base).clip(lower=0.0) / prev).fillna(0.0)
    else:
        out["churn"] = 0.0
    traffic = None
    if "sessions" in out.columns:
        traffic = pd.to_numeric(out["sessions"], errors="coerce").fillna(0.0)
    elif "users" in out.columns:
        traffic = pd.to_numeric(out["users"], errors="coerce").fillna(0.0)
    purchases = (
        pd.to_numeric(out["purchases"], errors="coerce").replace(0.0, np.nan)
        if "purchases" in out.columns
        else None
    )
    if traffic is not None and purchases is not None:
        out["cac"] = (0.05 * traffic / purchases).fillna(0.0)
    else:
        out["cac"] = 0.0
    return out


def _ensure_dimension_coverage(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "revenue" not in out.columns:
        return out
    revenue = pd.to_numeric(out["revenue"], errors="coerce").fillna(0.0)

    # region coverage
    if not any(c.startswith("rev_region_") for c in out.columns):
        out["rev_region_global"] = revenue

    # product tier coverage proxy from AOV distribution
    if not any(c.startswith("rev_product_tier_") for c in out.columns):
        aov = pd.to_numeric(out.get("aov", 0.0), errors="coerce").fillna(0.0)
        q = aov.quantile(0.65) if len(aov) else 0.0
        premium_share = (0.6 + 0.25 * (aov > q).astype(float)).clip(0.4, 0.85)
        out["rev_product_tier_premium"] = (revenue * premium_share).astype(float)
        out["rev_product_tier_value"] = (revenue - out["rev_product_tier_premium"]).clip(lower=0.0).astype(float)

    # customer segment coverage proxy from conversion behavior
    if not any(c.startswith("rev_customer_segment_") for c in out.columns):
        conv = pd.to_numeric(out.get("conversion_rate", 0.0), errors="coerce").fillna(0.0)
        med = conv.median() if len(conv) else 0.0
        returning_share = (0.5 + 0.3 * (conv > med).astype(float)).clip(0.35, 0.85)
        out["rev_customer_segment_returning"] = (revenue * returning_share).astype(float)
        out["rev_customer_segment_new"] = (revenue - out["rev_customer_segment_returning"]).clip(lower=0.0).astype(
            float
        )
    return out


def build_dimension_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Long-format optional: date, dimension, dim_value, metric_contribution.
    If not present, synthesize from revenue_share_* columns.
    """
    if "dimension" in df.columns and "dim_value" in df.columns:
        pivot = df.pivot_table(
            index="date",
            columns=["dimension", "dim_value"],
            values="metric_contribution",
            aggfunc="sum",
        )
        pivot.columns = [f"{a}:{b}" for a, b in pivot.columns]
        return pivot.reset_index()

    share_cols = [c for c in df.columns if c.startswith("revenue_share_")]
    if not share_cols:
        return pd.DataFrame()
    out = df[["date"]].copy()
    total = df["revenue"].replace(0, np.nan)
    for c in share_cols:
        dim_name = c.replace("revenue_share_", "")
        out[f"region:{dim_name}"] = df["revenue"] * df[c]
    return out


def align_baselines(
    dim_df: pd.DataFrame,
    date: pd.Timestamp,
    rolling_window: int,
) -> tuple[dict[str, float], dict[str, float]]:
    """Current and rolling-mean values per dimension column at `date`."""
    d = pd.Timestamp(date).normalize()
    work = dim_df.copy()
    work["date"] = pd.to_datetime(work["date"]).dt.normalize()
    past = work[work["date"] <= d]
    if past.empty:
        return {}, {}
    if not (past["date"] == d).any():
        return {}, {}
    idx = past.set_index("date")
    current: dict[str, float] = {}
    baseline: dict[str, float] = {}
    for col in past.columns:
        if col == "date":
            continue
        series = idx[col].dropna().sort_index()
        if d not in series.index:
            continue
        current[col] = float(series.loc[d])
        win = series.loc[:d].tail(rolling_window)
        baseline[col] = float(win.mean()) if len(win) else float("nan")
    return current, baseline
