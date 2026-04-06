from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import pandas as pd

from enterprise_decision_intel.controller import CentralController
from enterprise_decision_intel.data_pipeline import align_baselines, load_ga4_style_csv
from enterprise_decision_intel.shared_memory import SharedMemory


def _wide_dim_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("rev_region_") or c.startswith("rev_channel_")]


def _dim_key(col: str) -> str:
    if col.startswith("rev_region_"):
        return "region:" + col.replace("rev_region_", "")
    if col.startswith("rev_channel_"):
        return "channel:" + col.replace("rev_channel_", "")
    return col


def build_dim_frame(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["date"] + _wide_dim_columns(df)
    if len(cols) < 2:
        return pd.DataFrame()
    return df[cols].copy()


def iter_replay(
    df: pd.DataFrame,
    metric_col: str = "revenue",
    rolling_window: int = 14,
) -> Iterator[dict[str, Any]]:
    df = df.sort_values("date").reset_index(drop=True)
    dates = pd.to_datetime(df["date"])
    series = df[metric_col].astype(float)
    dim_df = build_dim_frame(df)
    for i in range(len(df)):
        ts = dates.iloc[i]
        bundle: dict[str, Any] = {
            "series": series.iloc[: i + 1].reset_index(drop=True),
            "dates": dates.iloc[: i + 1].reset_index(drop=True),
            "metric_name": metric_col,
            "dim_current": {},
            "dim_baseline": {},
        }
        if not dim_df.empty:
            cur, base = align_baselines(dim_df, ts, rolling_window)
            bundle["dim_current"] = {_dim_key(k): v for k, v in cur.items()}
            bundle["dim_baseline"] = {_dim_key(k): v for k, v in base.items()}
        yield bundle


@dataclass
class RunResult:
    rows: list[dict[str, Any]]


def run_dataset_from_df(
    df: pd.DataFrame,
    metric_col: str = "revenue",
    rolling_window: int = 14,
) -> RunResult:
    ctrl = CentralController()
    out: list[dict[str, Any]] = []
    for bundle in iter_replay(df, metric_col=metric_col, rolling_window=rolling_window):
        state = SharedMemory()
        state = ctrl.run_cycle(state, bundle)
        state = ctrl.maybe_reevaluate(state, bundle)
        snap = state.snapshot()
        snap["date"] = bundle["dates"].iloc[-1].isoformat()
        out.append(snap)
    return RunResult(rows=out)


def run_dataset(
    csv_path: str | Path,
    metric_col: str = "revenue",
    rolling_window: int = 14,
) -> RunResult:
    df = load_ga4_style_csv(csv_path)
    return run_dataset_from_df(df, metric_col=metric_col, rolling_window=rolling_window)


def last_anomaly_report(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for r in reversed(rows):
        if r.get("is_anomaly"):
            return r
    return None
