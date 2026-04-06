from __future__ import annotations

from typing import Any

from enterprise_decision_intel.config import (
    ControllerConfig,
    CorrectiveAction,
    DEFAULT_ACTIONS,
    default_utility_weights,
)
from enterprise_decision_intel.shared_memory import SharedMemory


class DecisionAgent:
    """Ranks predefined actions; utility is base score plus a small root-cause-aware boost."""

    def __init__(
        self,
        actions: list[CorrectiveAction] | None = None,
        ctrl: ControllerConfig | None = None,
    ) -> None:
        self.actions = actions or list(DEFAULT_ACTIONS)
        self.ctrl = ctrl or ControllerConfig()
        self.weights = default_utility_weights()

    def _utility(self, a: CorrectiveAction) -> float:
        return (
            self.weights["impact"] * a.expected_impact
            - self.weights["risk"] * a.risk_variance
            - self.weights["cost"] * (a.operational_cost / 5.0)
        )

    def _context_boost(self, action_id: str, root_causes: list[dict[str, Any]]) -> tuple[float, str]:
        """Tie-breaker so rankings shift when top attribution is channel vs region vs funnel signals."""
        if not root_causes:
            return 0.0, ""
        top = root_causes[0]
        dim = str(top.get("dimension") or "").lower()
        val = str(top.get("value") or "").lower()
        note = ""
        b = 0.0
        if dim == "channel":
            if action_id == "promo_surge":
                b += 0.12
                note = "channel-led deviation → favor channel spend fix"
            elif action_id in ("creative_refresh", "audience_retarget", "search_shopping_feed"):
                b += 0.08
                note = "channel-led deviation → creative, audience, or listing fixes"
            elif action_id == "checkout_audit" and any(x in val for x in ("direct", "organic", "referral")):
                b += 0.04
                note = "traffic mix → light funnel check"
        elif dim == "region":
            if action_id == "geo_campaign":
                b += 0.12
                note = "region-led deviation → favor regional campaign"
            elif action_id == "partnerships_local":
                b += 0.09
                note = "region-led deviation → local / affiliate push"
            elif action_id == "inventory_rebalance":
                b += 0.05
                note = "region mix → inventory / tier focus"
        if any(k in val for k in ("paid", "cpc", "ads")):
            if action_id == "promo_surge":
                b += 0.06
                note = "paid channel stress → promotional push"
            elif action_id in ("creative_refresh", "audience_retarget"):
                b += 0.05
                note = "paid traffic stress → creative or retargeting"
        if b and not note:
            note = "context adjustment from top attribution"
        return b, note

    def run(self, state: SharedMemory) -> SharedMemory:
        rcs = state.root_causes or []
        scored: list[tuple[float, CorrectiveAction, float, float, str]] = []
        for a in self.actions:
            base = self._utility(a)
            boost, note = self._context_boost(a.id, rcs)
            scored.append((base + boost, a, base, boost, note))

        scored.sort(key=lambda x: -x[0])
        utilities = [u for u, _, _, _, _ in scored]
        marginal = False
        if len(utilities) >= 2:
            top, second = utilities[0], utilities[1]
            if top > 0 and (top - second) / top < self.ctrl.marginal_utility_ratio:
                marginal = True
        ranked = []
        for total, a, base, boost, note in scored:
            ranked.append(
                {
                    **a.to_dict(),
                    "utility": round(float(total), 4),
                    "utility_base": round(float(base), 4),
                    "context_boost": round(float(boost), 4),
                    "why_ranked": note or "base utility from impact / risk / cost",
                }
            )
        state.ranked_actions = ranked
        if marginal:
            state.controller_notes.append("Top actions close in utility; showing ranked alternatives.")
        return state
