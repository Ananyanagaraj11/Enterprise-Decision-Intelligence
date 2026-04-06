from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from enterprise_decision_intel.config import DetectionConfig


def baseline_static_threshold(
    df: pd.DataFrame,
    metric_col: str,
    *,
    calib_rows: int = 35,
    low_q: float = 0.06,
    high_q: float = 0.94,
) -> tuple[list[bool], dict[str, Any]]:
    s = df[metric_col].astype(float)
    calib = min(calib_rows, max(10, len(df) // 3))
    ref = s.iloc[:calib]
    lo = float(ref.quantile(low_q))
    hi = float(ref.quantile(high_q))
    pred = [bool(x < lo or x > hi) for x in s]
    return pred, {"lo": lo, "hi": hi, "name": "static_threshold"}


def baseline_z_only(
    df: pd.DataFrame,
    metric_col: str,
    cfg: DetectionConfig,
    *,
    z_threshold: float | None = None,
) -> tuple[list[bool], dict[str, Any]]:
    """Rolling z only (no controller); optional different threshold vs agent."""

    thr = z_threshold if z_threshold is not None else cfg.z_threshold
    s = df[metric_col].astype(float)
    rm = s.rolling(cfg.rolling_window, min_periods=max(3, cfg.rolling_window // 2)).mean()
    rstd = s.rolling(cfg.rolling_window, min_periods=max(3, cfg.rolling_window // 2)).std()
    pred: list[bool] = []
    for i in range(len(s)):
        mu = rm.iloc[i]
        sig = rstd.iloc[i]
        x = s.iloc[i]
        if not np.isfinite(mu) or not np.isfinite(sig) or not np.isfinite(x):
            pred.append(False)
            continue
        sig = max(float(sig), cfg.min_std_floor)
        z = abs(float(x) - float(mu)) / sig
        pred.append(z >= thr)
    return pred, {"z_threshold": thr, "name": "z_only"}


def baseline_manual_script(
    df: pd.DataFrame,
    metric_col: str,
    *,
    pct_change: float = 0.16,
) -> tuple[list[bool], dict[str, Any]]:
    """Day-over-day percent change on revenue (non-agentic script proxy)."""

    s = df[metric_col].astype(float)
    pred: list[bool] = []
    pred.append(False)
    for i in range(1, len(s)):
        prev = float(s.iloc[i - 1])
        cur = float(s.iloc[i])
        ch = abs(cur - prev) / max(abs(prev), 1e-9)
        pred.append(ch >= pct_change)
    return pred, {"pct_change": pct_change, "name": "manual_script"}


def baseline_random_action_utility(cfg_actions_utility: list[float]) -> float:
    if not cfg_actions_utility:
        return 0.0
    return float(np.mean(cfg_actions_utility))
