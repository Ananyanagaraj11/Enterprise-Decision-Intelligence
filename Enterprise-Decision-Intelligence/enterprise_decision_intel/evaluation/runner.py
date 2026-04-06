from __future__ import annotations

import time
from typing import Any

import pandas as pd

from enterprise_decision_intel.config import DEFAULT_ACTIONS, DetectionConfig, default_utility_weights
from enterprise_decision_intel.data_pipeline import load_ga4_style_csv
from enterprise_decision_intel.evaluation.baselines_eval import (
    baseline_manual_script,
    baseline_random_action_utility,
    baseline_static_threshold,
    baseline_z_only,
)
from enterprise_decision_intel.evaluation.injection import InjectionResult, inject_controlled_anomalies, oracle_z_labels
from enterprise_decision_intel.evaluation.metrics import (
    action_ranking_consistency,
    detection_metrics,
    latency_summary,
    mean_top_utility,
    root_cause_accuracy,
    utility_gain_vs_baseline,
)
from enterprise_decision_intel.pipeline import run_dataset_from_df


def _utility_list() -> list[float]:
    w = default_utility_weights()
    out: list[float] = []
    for a in DEFAULT_ACTIONS:
        out.append(
            w["impact"] * a.expected_impact
            - w["risk"] * a.risk_variance
            - w["cost"] * (a.operational_cost / 5.0)
        )
    return out


def _impact_rank_ids() -> list[str]:
    return [a.id for a in sorted(DEFAULT_ACTIONS, key=lambda x: -x.expected_impact)]


def run_evaluation(
    df: pd.DataFrame,
    *,
    mode: str = "inject",
    inject_events: int = 10,
    seed: int = 42,
    metric_col: str = "revenue",
    rolling_window: int = 14,
    oracle_z: float = 3.45,
    z_only_threshold: float = 3.0,
    injection: InjectionResult | None = None,
    include_traces: bool = False,
) -> dict[str, Any]:
    """
    mode:
      - inject: controlled spikes + ground-truth keys (recommended for F1 / RCA accuracy)
      - oracle: y_true from strict rolling z (proxy; document limitation)
    """

    cfg = DetectionConfig(rolling_window=rolling_window)
    gt_keys: list[str | None]
    y_true: list[bool]

    if injection is not None:
        work = injection.df
        y_true = injection.anomaly_flags
        gt_keys = injection.root_cause_keys
    elif mode == "inject":
        inj = inject_controlled_anomalies(df, inject_events, seed=seed)
        work = inj.df
        y_true = inj.anomaly_flags
        gt_keys = inj.root_cause_keys
    elif mode == "oracle":
        work = df.copy()
        s = work[metric_col].astype(float)
        y_true = oracle_z_labels(s, rolling_window, oracle_z, cfg.min_std_floor)
        gt_keys = [None] * len(work)
    else:
        raise ValueError("mode must be 'inject' or 'oracle'")

    t0 = time.perf_counter()
    result = run_dataset_from_df(work, metric_col=metric_col, rolling_window=rolling_window)
    total_ms = (time.perf_counter() - t0) * 1000.0
    traces = result.rows
    n = len(traces)
    per_day_ms = [total_ms / max(n, 1)] * n

    y_agent = [bool(r.get("is_anomaly")) for r in traces]
    b1, meta1 = baseline_static_threshold(work, metric_col)
    b2, meta2 = baseline_z_only(work, metric_col, cfg, z_threshold=z_only_threshold)
    b3, meta3 = baseline_manual_script(work, metric_col)

    det_agent = detection_metrics(y_true, y_agent)
    det_b1 = detection_metrics(y_true, b1)
    det_b2 = detection_metrics(y_true, b2)
    det_b3 = detection_metrics(y_true, b3)

    rc1 = root_cause_accuracy(traces, gt_keys, 1)
    rc3 = root_cause_accuracy(traces, gt_keys, 3)

    mu = mean_top_utility(traces)
    rand_u = baseline_random_action_utility(_utility_list())
    ug = utility_gain_vs_baseline(mu["mean_top1_utility"], rand_u)

    first_ranked: list[str] = []
    for r in traces:
        acts = r.get("ranked_actions") or []
        if acts:
            first_ranked = [a["id"] for a in acts]
            break
    ars = action_ranking_consistency(_impact_rank_ids(), first_ranked) if first_ranked else {"kendall_tau": 0.0, "n": 0.0}

    lat = latency_summary(per_day_ms)

    conf_when_pos = [float(r.get("confidence") or 0.0) for r, t in zip(traces, y_true) if t]
    conf_calibration = {
        "mean_confidence_on_true_anomaly_days": float(sum(conf_when_pos) / len(conf_when_pos))
        if conf_when_pos
        else 0.0,
        "note": "Cohen kappa for explanations needs human rubric; not automated here.",
    }

    out: dict[str, Any] = {
        "mode": mode,
        "rows": n,
        "definitions": {
            "agentic_detector": "rolling mean/std z-threshold (see DetectionConfig)",
            "baseline_1": "global percentile bounds on early calibration window",
            "baseline_2": f"rolling z only, threshold={z_only_threshold} (stricter than agent default 2.5)",
            "baseline_3": "manual script: day-over-day percent change",
            "root_cause_gt": "injected dimension key (inject mode) or unavailable (oracle mode)",
            "utility_baseline": "mean utility if actions were chosen uniformly at random",
        },
        "baselines_meta": {"static": meta1, "z_only": meta2, "manual_script": meta3},
        "detection": {
            "agentic_system": det_agent,
            "baseline_1_static_threshold": det_b1,
            "baseline_2_z_only": det_b2,
            "baseline_3_manual_script": det_b3,
        },
        "root_cause": {"top1": rc1, "top3": rc3},
        "decision": {
            "mean_top1_utility": mu,
            "utility_vs_random_action_mean": ug,
            "ranking_consistency_vs_impact_order": ars,
        },
        "system": {
            "end_to_end_total_ms": float(total_ms),
            "per_day_processing_ms": lat,
            "confidence_proxy": conf_calibration,
        },
    }
    if include_traces:
        out["traces"] = traces
    return out


def run_evaluation_csv(path: str, **kwargs: Any) -> dict[str, Any]:
    df = load_ga4_style_csv(path)
    return run_evaluation(df, **kwargs)
