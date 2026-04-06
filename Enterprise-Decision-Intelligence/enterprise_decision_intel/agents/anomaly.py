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
        ewma = state.ewma_value
        if mu is None or sigma is None or x is None:
            state.is_anomaly = False
            state.anomaly_score = None
            state.z_score = None
            state.ewma_deviation = None
            state.confidence = 0.0
            state.flagged_for_review = True
            return state
        sigma = max(sigma, self.cfg.min_std_floor)
        z = abs(x - mu) / sigma
        ewma_dev = abs(x - ewma) / sigma if ewma is not None else z
        alpha = min(1.0, max(0.0, float(self.cfg.ewma_blend_alpha)))
        score = alpha * z + (1.0 - alpha) * ewma_dev

        state.z_score = float(z) if np.isfinite(z) else None
        state.ewma_deviation = float(ewma_dev) if np.isfinite(ewma_dev) else None
        state.anomaly_score = float(score) if np.isfinite(score) else None
        state.confidence = float(min(1.0, max(0.0, score / (thr * 1.2)))) if np.isfinite(score) else 0.0
        state.is_anomaly = bool(np.isfinite(score) and score >= thr)
        if not np.isfinite(score):
            state.is_anomaly = False
            state.confidence = 0.0
            state.flagged_for_review = True
        else:
            # Clear stale flag from earlier timesteps (shared memory persists across replay).
            state.flagged_for_review = False
        return state
