from __future__ import annotations

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

        state = self.monitoring.run(series, dates, metric_name, state)
        if state.rolling_mean is None and state.last_valid_baseline.get(metric_name) is not None:
            state.rolling_mean = state.last_valid_baseline[metric_name]
            state.controller_notes.append("Filled missing rolling stats from last validated baseline.")

        state = self.anomaly.run(state, strict=strict_anomaly)

        conf = state.confidence or 0.0
        if conf < self.detection.min_confidence:
            state.flagged_for_review = True
            state.root_causes = []
            state.ranked_actions = []
            state = self.explain.run(state)
            return state

        if not state.is_anomaly:
            state.root_causes = []
            state.ranked_actions = []
            state = self.explain.run(state)
            return state

        state = self.root_cause.run(state, dim_current, dim_baseline)
        state = self.decision.run(state)
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
        state.controller_notes.append("Re-evaluation pass (stricter anomaly gate).")
        return self.run_cycle(state, monitoring_bundle, strict_anomaly=True)
