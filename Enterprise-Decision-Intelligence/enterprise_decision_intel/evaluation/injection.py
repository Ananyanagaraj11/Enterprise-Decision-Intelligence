from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from enterprise_decision_intel.pipeline import _dim_key


def _wide_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("rev_region_") or c.startswith("rev_channel_")]


@dataclass
class InjectionResult:
    df: pd.DataFrame
    anomaly_flags: list[bool]
    root_cause_keys: list[str | None]


def inject_controlled_anomalies(
    df: pd.DataFrame,
    n_events: int,
    *,
    seed: int = 42,
    revenue_factor: float = 2.85,
    min_warmup: int = 20,
) -> InjectionResult:
    """
    Spike revenue and concentrate the lift in one dimension so contribution-based RCA has a clear target.
    Ground-truth key matches pipeline _dim_key(column).
    """

    work = df.copy()
    for c in [
        "revenue",
        "purchases",
        "sessions",
        "conversion_rate",
        "active_users",
        "line_items",
        "aov",
    ]:
        if c in work.columns:
            work[c] = work[c].astype(float)
    for c in _wide_cols(work):
        work[c] = work[c].astype(float)
    rng = np.random.default_rng(seed)
    n = len(work)
    if n <= min_warmup + 2:
        raise ValueError("Series too short for injection")
    cols = _wide_cols(work)
    if not cols:
        raise ValueError("Need rev_region_* / rev_channel_* columns for RCA ground truth")

    pool = list(range(min_warmup, n - 1))
    pick = rng.choice(pool, size=min(n_events, len(pool)), replace=False)

    flags = [False] * n
    keys: list[str | None] = [None] * n

    for i in pick:
        tgt = str(rng.choice(cols))
        keys[i] = _dim_key(tgt)
        flags[i] = True
        old_rev = float(work.at[i, "revenue"])
        new_rev = old_rev * revenue_factor
        work.at[i, "revenue"] = new_rev
        scale = new_rev / max(old_rev, 1e-9)
        for c in cols:
            work.at[i, c] = float(work.at[i, c]) * scale
        work.at[i, tgt] = float(work.at[i, tgt]) * 1.42
        s_dim = sum(float(work.at[i, c]) for c in cols)
        if s_dim > 1e-12:
            for c in cols:
                work.at[i, c] = float(work.at[i, c]) * (new_rev / s_dim)

        if "purchases" in work.columns:
            work.at[i, "purchases"] = float(work.at[i, "purchases"]) * min(revenue_factor, 1.8)
        if "sessions" in work.columns:
            work.at[i, "sessions"] = float(work.at[i, "sessions"]) * min(1.0 + (revenue_factor - 1.0) * 0.35, 1.5)
        if "active_users" in work.columns:
            work.at[i, "active_users"] = float(work.at[i, "active_users"]) * min(
                1.0 + (revenue_factor - 1.0) * 0.35, 1.5
            )
        if "line_items" in work.columns:
            work.at[i, "line_items"] = float(work.at[i, "line_items"]) * min(
                1.0 + (revenue_factor - 1.0) * 0.35, 1.5
            )
        if "conversion_rate" in work.columns and "sessions" in work.columns:
            ssn = float(work.at[i, "sessions"])
            work.at[i, "conversion_rate"] = float(work.at[i, "purchases"]) / max(ssn, 1e-9)
        if "aov" in work.columns and "purchases" in work.columns:
            work.at[i, "aov"] = float(work.at[i, "revenue"]) / max(float(work.at[i, "purchases"]), 1e-9)

    return InjectionResult(df=work, anomaly_flags=flags, root_cause_keys=keys)


def oracle_z_labels(
    series: pd.Series,
    rolling_window: int,
    z_thr: float,
    min_std_floor: float = 1e-6,
) -> list[bool]:
    """Independent strict z-score labels (for natural-data experiments; document as proxy oracle)."""

    s = series.astype(float)
    rm = s.rolling(rolling_window, min_periods=max(3, rolling_window // 2)).mean()
    rstd = s.rolling(rolling_window, min_periods=max(3, rolling_window // 2)).std()
    out: list[bool] = []
    for i in range(len(s)):
        mu = rm.iloc[i]
        sig = rstd.iloc[i]
        x = s.iloc[i]
        if not np.isfinite(mu) or not np.isfinite(sig) or not np.isfinite(x):
            out.append(False)
            continue
        sig = max(float(sig), min_std_floor)
        z = abs(float(x) - float(mu)) / sig
        out.append(z >= z_thr)
    return out
