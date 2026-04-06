from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class SharedMemory:
    """Structured state passed between agents (GA4-derived metrics → decisions)."""

    timestamp: datetime | None = None
    metric_name: str = ""
    current_value: float | None = None
    rolling_mean: float | None = None
    rolling_std: float | None = None
    ewma_value: float | None = None
    anomaly_score: float | None = None
    confidence: float | None = None
    is_anomaly: bool = False
    flagged_for_review: bool = False
    root_causes: list[dict[str, Any]] = field(default_factory=list)
    ranked_actions: list[dict[str, Any]] = field(default_factory=list)
    explanation_text: str = ""
    controller_notes: list[str] = field(default_factory=list)
    reeval_round: int = 0
    last_valid_baseline: dict[str, float] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "rolling_mean": self.rolling_mean,
            "rolling_std": self.rolling_std,
            "ewma_value": self.ewma_value,
            "anomaly_score": self.anomaly_score,
            "confidence": self.confidence,
            "is_anomaly": self.is_anomaly,
            "flagged_for_review": self.flagged_for_review,
            "root_causes": list(self.root_causes),
            "ranked_actions": list(self.ranked_actions),
            "explanation_text": self.explanation_text,
            "controller_notes": list(self.controller_notes),
            "reeval_round": self.reeval_round,
        }


def parse_date_key(d: date | datetime | str) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return datetime.fromisoformat(str(d)[:10]).date()
