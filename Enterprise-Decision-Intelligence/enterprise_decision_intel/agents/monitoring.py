from __future__ import annotations

import numpy as np
import pandas as pd

from enterprise_decision_intel.config import DetectionConfig
from enterprise_decision_intel.shared_memory import SharedMemory


class MonitoringAgent:
    def __init__(self, cfg: DetectionConfig | None = None) -> None:
        self.cfg = cfg or DetectionConfig()

    def run(
        self,
        series: pd.Series,
        dates: pd.DatetimeIndex,
        metric_name: str,
        state: SharedMemory,
    ) -> SharedMemory:
        s = series.astype(float)
        rm = s.rolling(self.cfg.rolling_window, min_periods=max(3, self.cfg.rolling_window // 2)).mean()
        rstd = s.rolling(self.cfg.rolling_window, min_periods=max(3, self.cfg.rolling_window // 2)).std()
        ewma = s.ewm(span=self.cfg.ewma_span, adjust=False).mean()
        idx = len(s) - 1
        state.metric_name = metric_name
        state.timestamp = pd.Timestamp(dates[idx]).to_pydatetime()
        state.current_value = float(s.iloc[idx])
        state.rolling_mean = float(rm.iloc[idx]) if np.isfinite(rm.iloc[idx]) else None
        state.rolling_std = float(rstd.iloc[idx]) if np.isfinite(rstd.iloc[idx]) else None
        state.ewma_value = float(ewma.iloc[idx]) if np.isfinite(ewma.iloc[idx]) else None
        if state.rolling_mean is not None:
            state.last_valid_baseline[metric_name] = state.rolling_mean
        return state
