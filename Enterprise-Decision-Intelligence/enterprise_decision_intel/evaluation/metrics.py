from __future__ import annotations

import statistics
from typing import Any, Sequence

from scipy.stats import kendalltau

from enterprise_decision_intel.baselines import precision_recall_f1


def detection_metrics(y_true: Sequence[bool], y_pred: Sequence[bool]) -> dict[str, float]:
    return precision_recall_f1(list(y_true), list(y_pred))


def latency_summary(latency_ms: Sequence[float]) -> dict[str, float]:
    xs = sorted(float(x) for x in latency_ms)
    if not xs:
        return {"mean_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "total_ms": 0.0}
    n = len(xs)
    p50 = xs[n // 2]
    p95 = xs[int(0.95 * (n - 1))]
    return {
        "mean_ms": float(statistics.mean(xs)),
        "p50_ms": float(p50),
        "p95_ms": float(p95),
        "total_ms": float(sum(xs)),
    }


def root_cause_accuracy(
    traces: list[dict[str, Any]],
    gt_keys: list[str | None],
    top_k: int,
) -> dict[str, float]:
    """Top-k on all days with a ground-truth key (injected); misses count as failures."""

    eligible = 0
    hits = 0
    for row, gt in zip(traces, gt_keys):
        if not gt:
            continue
        eligible += 1
        if not row.get("is_anomaly"):
            continue
        rcs = row.get("root_causes") or []
        if not rcs:
            continue
        ranked = [f"{r['dimension']}:{r['value']}" for r in rcs[:top_k]]
        if gt in ranked:
            hits += 1
    acc = hits / eligible if eligible else 0.0
    return {"top_k": float(top_k), "accuracy": float(acc), "eligible_days": float(eligible), "hits": float(hits)}


def mean_top_utility(traces: list[dict[str, Any]]) -> dict[str, float]:
    vals: list[float] = []
    for row in traces:
        if not row.get("is_anomaly"):
            continue
        acts = row.get("ranked_actions") or []
        if acts:
            vals.append(float(acts[0]["utility"]))
    return {
        "mean_top1_utility": float(statistics.mean(vals)) if vals else 0.0,
        "anomaly_days_with_actions": float(len(vals)),
    }


def utility_gain_vs_baseline(
    agent_mean_utility: float,
    baseline_mean_utility: float,
) -> dict[str, float]:
    return {
        "agent_mean_utility": float(agent_mean_utility),
        "baseline_mean_utility": float(baseline_mean_utility),
        "gain": float(agent_mean_utility - baseline_mean_utility),
    }


def action_ranking_consistency(
    ranked_ids_a: list[str],
    ranked_ids_b: list[str],
) -> dict[str, float]:
    """Kendall tau between two orderings of the same action ids (1.0 = identical rank)."""

    if not ranked_ids_a or not ranked_ids_b or set(ranked_ids_a) != set(ranked_ids_b):
        return {"kendall_tau": 0.0, "n": 0.0}
    order = {a: i for i, a in enumerate(ranked_ids_a)}
    y = [order[x] for x in ranked_ids_b]
    x = list(range(len(y)))
    tau, _ = kendalltau(x, y)
    if tau != tau:
        tau = 0.0
    return {"kendall_tau": float(tau), "n": float(len(y))}
