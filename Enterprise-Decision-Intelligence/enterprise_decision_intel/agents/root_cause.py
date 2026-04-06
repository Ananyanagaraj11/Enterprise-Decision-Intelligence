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
        devs: list[tuple[str, float, float, float]] = []
        for k, cur in current_by_dim.items():
            base = baseline_by_dim.get(k)
            if base is None or not np.isfinite(base) or not np.isfinite(cur):
                continue
            devs.append((k, abs(cur - base), float(cur), float(base)))
        total = sum(d for _, d, _, _ in devs)
        if total <= 1e-12:
            state.root_causes = []
            state.root_causes_ranked = []
            state.top1_root_cause = None
            state.top3_root_causes = []
            return state
        sorted_devs = sorted(devs, key=lambda x: -x[1])
        for k, d, cur, base in sorted_devs:
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
                    "current": round(cur, 4),
                    "baseline": round(base, 4),
                }
            )
        # Multiple equal top contributors are all surfaced.
        if len(rows) > 1 and abs(rows[0]["contribution_pct"] - rows[1]["contribution_pct"]) < 1e-9:
            state.controller_notes.append("Multiple equal top root causes; reporting all tied contributors.")
        state.root_causes = rows
        state.root_causes_ranked = rows
        state.top1_root_cause = f"{rows[0]['dimension']}:{rows[0]['value']}" if rows else None
        state.top3_root_causes = [f"{r['dimension']}:{r['value']}" for r in rows[:3]]
        return state
