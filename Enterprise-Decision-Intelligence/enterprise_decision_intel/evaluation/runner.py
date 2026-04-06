from __future__ import annotations

import time
from typing import Any

import pandas as pd
from scipy.stats import ttest_rel

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
from enterprise_decision_intel.shared_memory import SharedMemory
from enterprise_decision_intel.controller import CentralController


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


def evaluation_table(report: dict[str, Any]) -> pd.DataFrame:
    det = report["detection"]
    rows = []
    for key, vals in det.items():
        rows.append(
            {
                "system": key,
                "precision": vals["precision"],
                "recall": vals["recall"],
                "f1": vals["f1"],
            }
        )
    rows.append(
        {
            "system": "root_cause_top1",
            "precision": None,
            "recall": None,
            "f1": report["root_cause"]["top1"]["accuracy"],
        }
    )
    rows.append(
        {
            "system": "root_cause_top3",
            "precision": None,
            "recall": None,
            "f1": report["root_cause"]["top3"]["accuracy"],
        }
    )
    rows.append(
        {
            "system": "decision_rank_consistency",
            "precision": None,
            "recall": None,
            "f1": report["decision"]["ranking_consistency_vs_impact_order"]["kendall_tau"],
        }
    )
    return pd.DataFrame(rows)


def run_advanced_evaluation(
    df: pd.DataFrame,
    *,
    metric_col: str = "revenue",
    runs: int = 3,
    base_seed: int = 42,
) -> dict[str, Any]:
    runs = max(3, min(5, int(runs)))
    run_reports: list[dict[str, Any]] = []
    agent_f1: list[float] = []
    baseline2_f1: list[float] = []
    for i in range(runs):
        rep = run_evaluation(
            df,
            mode="inject",
            inject_events=10,
            seed=base_seed + i,
            metric_col=metric_col,
        )
        run_reports.append(rep)
        agent_f1.append(float(rep["detection"]["agentic_system"]["f1"]))
        baseline2_f1.append(float(rep["detection"]["baseline_2_z_only"]["f1"]))

    t_stat, p_value = ttest_rel(agent_f1, baseline2_f1)
    if t_stat != t_stat:
        t_stat = 0.0
    if p_value != p_value:
        p_value = 1.0

    # Cohen's kappa placeholder using optional human rubric labels.
    kappa = None
    if "explanation_label_human_1" in df.columns and "explanation_label_human_2" in df.columns:
        h1 = pd.Series(df["explanation_label_human_1"]).astype(str)
        h2 = pd.Series(df["explanation_label_human_2"]).astype(str)
        obs = (h1 == h2).mean()
        p1 = h1.value_counts(normalize=True)
        p2 = h2.value_counts(normalize=True)
        cats = set(p1.index).union(set(p2.index))
        pe = sum(float(p1.get(c, 0.0)) * float(p2.get(c, 0.0)) for c in cats)
        kappa = float((obs - pe) / (1 - pe)) if (1 - pe) > 1e-12 else 0.0

    return {
        "runs": runs,
        "seeds": [base_seed + i for i in range(runs)],
        "agent_f1": agent_f1,
        "baseline2_f1": baseline2_f1,
        "paired_t_test_agent_vs_baseline2": {"t_stat": float(t_stat), "p_value": float(p_value)},
        "cohens_kappa_explanation": kappa,
        "note": "Kappa computed only when two human-rater label columns exist in input data.",
        "reports": run_reports,
    }


def conflict_reeval_smoke_test(df: pd.DataFrame, metric_col: str = "revenue") -> dict[str, Any]:
    """
    Force a controller conflict pattern (actions with empty RCA) and assert re-eval is triggered.
    """
    work = df.sort_values("date").reset_index(drop=True)
    if len(work) < 5:
        return {"ok": False, "reason": "dataset_too_short"}
    ctrl = CentralController()
    from enterprise_decision_intel.pipeline import iter_replay

    state = SharedMemory()
    bundles = list(iter_replay(work.head(8), metric_col=metric_col, rolling_window=14))
    if not bundles:
        return {"ok": False, "reason": "no_bundles"}
    state = ctrl.run_cycle(state, bundles[-1])
    # Inject conflict to force re-eval path.
    state.is_anomaly = True
    state.confidence = (ctrl.detection.min_confidence or 0.35) * 1.05
    state.root_causes = []
    state.ranked_actions = [{"id": "dummy", "utility": 0.1}]
    before = state.reeval_round
    state = ctrl.maybe_reevaluate(state, bundles[-1])
    after = state.reeval_round
    note_hit = any("Re-evaluation pass" in n for n in state.controller_notes)
    return {"ok": bool(after > before and note_hit), "reeval_round_before": before, "reeval_round_after": after}
