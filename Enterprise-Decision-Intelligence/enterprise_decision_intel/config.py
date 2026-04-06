from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DetectionConfig:
    rolling_window: int = 14
    ewma_span: int = 7
    z_threshold: float = 2.5
    min_confidence: float = 0.35
    min_std_floor: float = 1e-6


@dataclass(frozen=True)
class ControllerConfig:
    max_reeval_rounds: int = 1
    marginal_utility_ratio: float = 0.08


@dataclass
class CorrectiveAction:
    id: str
    label: str
    expected_impact: float
    risk_variance: float
    operational_cost: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "expected_impact": self.expected_impact,
            "risk_variance": self.risk_variance,
            "operational_cost": self.operational_cost,
        }


# Playbook of predefined interventions (proposal: fixed catalog + utility rank).
# Size is independent of dataset rows — add more rows here if the business scenario needs them.
DEFAULT_ACTIONS: list[CorrectiveAction] = [
    CorrectiveAction(
        "promo_surge",
        "Short promotional push on underperforming channel",
        expected_impact=0.72,
        risk_variance=0.12,
        operational_cost=2.0,
    ),
    CorrectiveAction(
        "inventory_rebalance",
        "Rebalance inventory / product tier focus",
        expected_impact=0.55,
        risk_variance=0.18,
        operational_cost=3.5,
    ),
    CorrectiveAction(
        "geo_campaign",
        "Regional campaign adjustment",
        expected_impact=0.68,
        risk_variance=0.15,
        operational_cost=2.8,
    ),
    CorrectiveAction(
        "checkout_audit",
        "Funnel / checkout experience audit",
        expected_impact=0.48,
        risk_variance=0.08,
        operational_cost=1.5,
    ),
    CorrectiveAction(
        "hold_and_observe",
        "Hold spend and monitor (low intervention)",
        expected_impact=0.22,
        risk_variance=0.05,
        operational_cost=0.5,
    ),
    CorrectiveAction(
        "creative_refresh",
        "Refresh creatives / landing pages for underperforming traffic",
        expected_impact=0.58,
        risk_variance=0.14,
        operational_cost=2.2,
    ),
    CorrectiveAction(
        "audience_retarget",
        "Retargeting / remarketing to high-intent segments",
        expected_impact=0.62,
        risk_variance=0.16,
        operational_cost=2.4,
    ),
    CorrectiveAction(
        "pricing_promo_test",
        "Limited-time price or bundle test on affected SKUs",
        expected_impact=0.52,
        risk_variance=0.22,
        operational_cost=2.9,
    ),
    CorrectiveAction(
        "site_reliability",
        "Technical review: latency, errors, mobile UX on key paths",
        expected_impact=0.44,
        risk_variance=0.09,
        operational_cost=2.0,
    ),
    CorrectiveAction(
        "crm_outreach",
        "CRM / email push to recover stalled carts or churn risk",
        expected_impact=0.5,
        risk_variance=0.11,
        operational_cost=1.8,
    ),
    CorrectiveAction(
        "search_shopping_feed",
        "Shopping feed & search listing hygiene (titles, GTIN, negatives)",
        expected_impact=0.54,
        risk_variance=0.13,
        operational_cost=2.1,
    ),
    CorrectiveAction(
        "partnerships_local",
        "Local or affiliate partnership push in stressed regions",
        expected_impact=0.46,
        risk_variance=0.17,
        operational_cost=3.0,
    ),
]

def default_utility_weights() -> dict[str, float]:
    return {"impact": 1.0, "risk": 0.35, "cost": 0.12}
