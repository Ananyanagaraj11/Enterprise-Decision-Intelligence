from __future__ import annotations

import numpy as np

from enterprise_decision_intel.config import DetectionConfig
from enterprise_decision_intel.shared_memory import SharedMemory


class AnomalyDetectionAgent:
    def __init__(self, cfg: DetectionConfig | None = None) -> None:
        self.cfg = cfg or DetectionConfig()

    def run(self, state: SharedMemory, strict: bool = False) -> SharedMemory:
        thr = self.cfg.z_threshold * (1.15 if strict else 1.0)
        mu = state.rolling_mean
        sigma = state.rolling_std
        x = state.current_value
        if mu is None or sigma is None or x is None:
            state.is_anomaly = False
            state.anomaly_score = None
            state.confidence = 0.0
            state.flagged_for_review = True
            return state
        sigma = max(sigma, self.cfg.min_std_floor)
        z = abs(x - mu) / sigma
        state.anomaly_score = float(z)
        state.confidence = float(min(1.0, z / (thr * 1.2)))
        state.is_anomaly = z >= thr
        if not np.isfinite(z):
            state.is_anomaly = False
            state.confidence = 0.0
            state.flagged_for_review = True
        return state
