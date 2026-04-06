from __future__ import annotations

from typing import Any

import numpy as np

from enterprise_decision_intel.config import DetectionConfig
from enterprise_decision_intel.shared_memory import SharedMemory


class RootCauseAgent:
    def __init__(self, cfg: DetectionConfig | None = None) -> None:
        self.cfg = cfg or DetectionConfig()

    def run(
        self,
        state: SharedMemory,
        current_by_dim: dict[str, float],
        baseline_by_dim: dict[str, float],
    ) -> SharedMemory:
        rows: list[dict[str, Any]] = []
        devs: list[tuple[str, float]] = []
        for k, cur in current_by_dim.items():
            base = baseline_by_dim.get(k)
            if base is None or not np.isfinite(base) or not np.isfinite(cur):
                continue
            devs.append((k, abs(cur - base)))
        total = sum(d for _, d in devs)
        if total <= 1e-12:
            state.root_causes = []
            return state
        for k, d in sorted(devs, key=lambda x: -x[1]):
            pct = 100.0 * d / total
            if ":" in k:
                dim_type, dim_val = k.split(":", 1)
            else:
                dim_type, dim_val = "factor", k
            rows.append(
                {
                    "dimension": dim_type,
                    "value": dim_val,
                    "contribution_pct": round(float(pct), 2),
                    "deviation": round(float(d), 4),
                }
            )
        state.root_causes = rows
        return state
