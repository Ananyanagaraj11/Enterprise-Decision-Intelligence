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
    if "aov" not in out.columns and "revenue" in out.columns and "purchases" in out.columns:
        r = pd.to_numeric(out["revenue"], errors="coerce").fillna(0.0)
        p = pd.to_numeric(out["purchases"], errors="coerce").replace(0.0, np.nan)
        out["aov"] = (r / p).fillna(0.0)
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
