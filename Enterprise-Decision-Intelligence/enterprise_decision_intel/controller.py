from __future__ import annotations

from typing import Any

from enterprise_decision_intel.agents.anomaly import AnomalyDetectionAgent
from enterprise_decision_intel.agents.decision import DecisionAgent
from enterprise_decision_intel.agents.explanation import ExplanationAgent
from enterprise_decision_intel.agents.monitoring import MonitoringAgent
from enterprise_decision_intel.agents.root_cause import RootCauseAgent
from enterprise_decision_intel.config import ControllerConfig, DetectionConfig
from enterprise_decision_intel.shared_memory import SharedMemory


class CentralController:
    """Rule-based stage gates: confidence thresholds, re-eval, empty state fallbacks."""

    def __init__(
        self,
        detection: DetectionConfig | None = None,
        ctrl: ControllerConfig | None = None,
    ) -> None:
        self.detection = detection or DetectionConfig()
        self.ctrl = ctrl or ControllerConfig()
        self.monitoring = MonitoringAgent(self.detection)
        self.anomaly = AnomalyDetectionAgent(self.detection)
        self.root_cause = RootCauseAgent(self.detection)
        self.decision = DecisionAgent(ctrl=self.ctrl)
        self.explain = ExplanationAgent()

    def _dimension_anomaly_scores(
        self, current_by_dim: dict[str, float], baseline_by_dim: dict[str, float]
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        abs_devs = []
        for k, cur in current_by_dim.items():
            base = baseline_by_dim.get(k)
            if base is None:
                continue
            d = abs(float(cur) - float(base))
            abs_devs.append((k, d))
        total = sum(v for _, v in abs_devs)
        if total <= 1e-12:
            return []
        for k, d in sorted(abs_devs, key=lambda x: -x[1]):
            rows.append({"dimension_key": k, "deviation_pct": round(100.0 * d / total, 2)})
        return rows

    def run_cycle(
        self,
        state: SharedMemory,
        monitoring_bundle: dict,
        strict_anomaly: bool = False,
    ) -> SharedMemory:
        series = monitoring_bundle["series"]
        dates = monitoring_bundle["dates"]
        metric_name = monitoring_bundle["metric_name"]
        dim_current = monitoring_bundle.get("dim_current") or {}
        dim_baseline = monitoring_bundle.get("dim_baseline") or {}
        human_approved = bool(monitoring_bundle.get("human_approved", False))

        state = self.monitoring.run(series, dates, metric_name, state)
        if state.current_value is None:
            state.flagged_for_review = True
            state.controller_notes.append("Missing current metric value; stopping cycle.")
            state = self.explain.run(state)
            return state
        if state.rolling_mean is None and state.last_valid_baseline.get(metric_name) is not None:
            state.rolling_mean = state.last_valid_baseline[metric_name]
            state.controller_notes.append("Filled missing rolling stats from last validated baseline.")

        state = self.anomaly.run(state, strict=strict_anomaly)
        state.dimension_anomaly_scores = self._dimension_anomaly_scores(dim_current, dim_baseline)

        conf = state.confidence or 0.0
        if conf < self.detection.min_confidence:
            state.flagged_for_review = True
            state.root_causes = []
            state.root_causes_ranked = []
            state.top1_root_cause = None
            state.top3_root_causes = []
            state.ranked_actions = []
            state.approval_required = False
            state.approved_for_execution = False
            state.execution_status = "stopped_low_confidence"
            state = self.explain.run(state)
            return state

        if not state.is_anomaly:
            state.root_causes = []
            state.root_causes_ranked = []
            state.top1_root_cause = None
            state.top3_root_causes = []
            state.ranked_actions = []
            state.approval_required = False
            state.approved_for_execution = False
            state.execution_status = "no_action_needed"
            state = self.explain.run(state)
            return state

        state = self.root_cause.run(state, dim_current, dim_baseline)
        state = self.decision.run(state)
        state.approval_required = self.ctrl.require_human_approval and bool(state.ranked_actions)
        if state.approval_required and not human_approved:
            state.approved_for_execution = False
            state.execution_status = "pending_human_approval"
            state.controller_notes.append("Decision prepared; waiting for human approval before execution.")
        else:
            state.approved_for_execution = bool(state.ranked_actions)
            state.execution_status = "approved_for_execution" if state.approved_for_execution else "not_requested"
        state = self.explain.run(state)
        return state

    def maybe_reevaluate(
        self,
        state: SharedMemory,
        monitoring_bundle: dict,
    ) -> SharedMemory:
        if state.reeval_round >= self.ctrl.max_reeval_rounds:
            return state
        conflict = False
        if state.is_anomaly and (state.confidence or 0) < self.detection.min_confidence * 1.1:
            conflict = True
        if state.ranked_actions and not state.root_causes and state.is_anomaly:
            conflict = True
        if not conflict:
            return state
        state.reeval_round += 1
        state.controller_notes.append(
            f"Re-evaluation pass {state.reeval_round}: stricter anomaly gate due to low-confidence/conflict output."
        )
        return self.run_cycle(state, monitoring_bundle, strict_anomaly=True)
