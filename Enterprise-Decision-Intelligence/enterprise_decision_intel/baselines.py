from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from enterprise_decision_intel.config import DetectionConfig


@dataclass
class BaselineStaticThreshold:
    """Fixed bounds on raw values (non-agentic baseline 1)."""

    lower: float
    upper: float

    def label(self, x: float) -> bool:
        return not (self.lower <= x <= self.upper)


@dataclass
class BaselineDetectionOnly:
    """Rolling z-score only — no attribution or actions (baseline 2)."""

    cfg: DetectionConfig

    def zscore(self, series: pd.Series) -> tuple[float, float, float]:
        cfg = self.cfg
        rm = series.rolling(cfg.rolling_window, min_periods=max(3, cfg.rolling_window // 2)).mean()
        rstd = series.rolling(cfg.rolling_window, min_periods=max(3, cfg.rolling_window // 2)).std()
        idx = len(series) - 1
        x = float(series.iloc[idx])
        mu = float(rm.iloc[idx])
        sig = max(float(rstd.iloc[idx]), cfg.min_std_floor)
        z = abs(x - mu) / sig
        return z, mu, sig


def manual_script_stub(
    df: pd.DataFrame,
    metric: str = "revenue",
) -> dict[str, Any]:
    """Baseline 3 placeholder: independent pulls without shared state (returns simple stats)."""

    s = df[metric].astype(float)
    return {
        "mean": float(s.mean()),
        "std": float(s.std()),
        "last": float(s.iloc[-1]),
        "note": "manual aggregation script baseline — no coordinated agents",
    }


def precision_recall_f1(y_true: list[bool], y_pred: list[bool]) -> dict[str, float]:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
    fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {"precision": prec, "recall": rec, "f1": f1}
