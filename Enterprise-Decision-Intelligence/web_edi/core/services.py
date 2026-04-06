"""Build dashboard context from GA4 CSV + agentic pipeline (readable copy, chart payloads)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from enterprise_decision_intel.config import DetectionConfig
from enterprise_decision_intel.data_pipeline import load_ga4_style_csv
from enterprise_decision_intel.evaluation.injection import inject_controlled_anomalies
from enterprise_decision_intel.evaluation.runner import run_evaluation
from enterprise_decision_intel.pipeline import run_dataset_from_df

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _human_date(s: str | None) -> str:
    if not s:
        return "—"
    try:
        return pd.Timestamp(s).strftime("%b %d, %Y")
    except Exception:
        return str(s)[:10]


def _is_currency_metric(metric: str) -> bool:
    return metric in ("revenue", "aov")


def _norm_series(s: pd.Series) -> list[float | None]:
    """Min–max normalize to [0, 1] for overlay charts (per-series)."""
    v = pd.to_numeric(s, errors="coerce")
    lo, hi = float(v.min()), float(v.max())
    if hi - lo < 1e-12:
        return [0.5 if pd.notna(x) else None for x in v]
    out: list[float | None] = []
    for x in v:
        if pd.isna(x):
            out.append(None)
        else:
            out.append((float(x) - lo) / (hi - lo))
    return out


def _fmt_num(x: Any, currency: bool = False) -> str:
    if x is None:
        return "—"
    try:
        v = float(x)
        if currency:
            return f"${v:,.0f}" if v >= 100 else f"${v:,.2f}"
        if abs(v) >= 1000:
            return f"{v:,.1f}"
        return f"{v:.2f}"
    except (TypeError, ValueError):
        return str(x)


def build_context(
    csv_path: Path,
    *,
    metric: str = "revenue",
    window: int = 14,
    run_eval: bool = True,
    inject_events: int = 8,
    seed: int = 42,
    day_index: int | None = None,
) -> dict[str, Any]:
    df = load_ga4_style_csv(csv_path)
    if metric not in df.columns:
        raise ValueError(f"Column {metric} not in CSV")

    report: dict | None = None
    traces: list[dict] = []

    if run_eval:
        inj = inject_controlled_anomalies(df, inject_events, seed=seed)
        report = run_evaluation(
            df,
            mode="inject",
            injection=inj,
            metric_col=metric,
            rolling_window=window,
            include_traces=True,
        )
        traces = list(report.pop("traces", []) or [])
        df_plot = inj.df
    else:
        result = run_dataset_from_df(df, metric_col=metric, rolling_window=window)
        traces = result.rows
        df_plot = df

    d = df_plot.sort_values("date").reset_index(drop=True)
    dates = pd.to_datetime(d["date"])
    y = d[metric].astype(float)
    cfg = DetectionConfig(rolling_window=window)
    rm = y.rolling(cfg.rolling_window, min_periods=max(3, cfg.rolling_window // 2)).mean()
    rstd = y.rolling(cfg.rolling_window, min_periods=max(3, cfg.rolling_window // 2)).std()

    labels = [d.strftime("%b %d") for d in dates]
    values = [float(v) if pd.notna(v) else None for v in y]
    rolling = [float(v) if pd.notna(v) else None for v in rm]
    anom = [bool(traces[i].get("is_anomaly")) for i in range(len(traces))]

    z_scores: list[float | None] = []
    for i in range(len(y)):
        mu = rm.iloc[i]
        sig = rstd.iloc[i]
        xv = y.iloc[i]
        if pd.notna(mu) and pd.notna(sig) and pd.notna(xv) and float(sig) > 1e-9:
            z_scores.append(abs(float(xv) - float(mu)) / float(sig))
        else:
            z_scores.append(None)

    anom_indices = [i for i, t in enumerate(traces) if t.get("is_anomaly")]
    if day_index is not None and traces and 0 <= day_index < len(traces):
        pick_i = day_index
    else:
        pick_i = anom_indices[-1] if anom_indices else (len(traces) - 1 if traces else 0)
    sel = traces[pick_i] if traces else {}

    ml = metric.replace("_", " ")
    summary_html = ""
    if sel:
        is_anom = bool(sel.get("is_anomaly"))
        if is_anom:
            summary_html = (
                f"<p class='text-slate-700 leading-relaxed'>On <strong>{_human_date(str(sel.get('date')))}</strong>, "
                f"<strong>{ml}</strong> was <strong>{_fmt_num(sel.get('current_value'), _is_currency_metric(metric))}</strong> — "
                f"outside the usual band (baseline near <strong>{_fmt_num(sel.get('rolling_mean'), _is_currency_metric(metric))}</strong>). "
                f"Flagged as an <strong>anomaly</strong> with confidence <strong>{_fmt_num(sel.get('confidence'))}</strong>.</p>"
            )
        else:
            summary_html = (
                f"<p class='text-slate-700 leading-relaxed'>On <strong>{_human_date(str(sel.get('date')))}</strong>, "
                f"<strong>{ml}</strong> matches the rolling baseline — <strong>no root-cause step</strong> on normal days.</p>"
            )

    detection = report.get("detection", {}) if report else {}
    f1_chart = {
        "labels": ["Agent", "Static bounds", "Z-only", "Manual %Δ"],
        "values": [
            (detection.get("agentic_system") or {}).get("f1", 0),
            (detection.get("baseline_1_static_threshold") or {}).get("f1", 0),
            (detection.get("baseline_2_z_only") or {}).get("f1", 0),
            (detection.get("baseline_3_manual_script") or {}).get("f1", 0),
        ],
    }
    pr_chart = {
        "labels": ["Agent", "B1", "B2", "B3"],
        "datasets": [
            {
                "label": "Precision",
                "data": [
                    (detection.get("agentic_system") or {}).get("precision", 0),
                    (detection.get("baseline_1_static_threshold") or {}).get("precision", 0),
                    (detection.get("baseline_2_z_only") or {}).get("precision", 0),
                    (detection.get("baseline_3_manual_script") or {}).get("precision", 0),
                ],
            },
            {
                "label": "Recall",
                "data": [
                    (detection.get("agentic_system") or {}).get("recall", 0),
                    (detection.get("baseline_1_static_threshold") or {}).get("recall", 0),
                    (detection.get("baseline_2_z_only") or {}).get("recall", 0),
                    (detection.get("baseline_3_manual_script") or {}).get("recall", 0),
                ],
            },
        ],
    }

    day_options = []
    for i, t in enumerate(traces):
        day_options.append(
            {
                "i": i,
                "label": f"{_human_date(str(t.get('date')))} · {'Anomaly' if t.get('is_anomaly') else 'Normal'}",
                "is_anomaly": bool(t.get("is_anomaly")),
            }
        )

    chart_norm: str | None = None
    norm_sets: list[dict[str, Any]] = []
    if "revenue" in d.columns:
        norm_sets.append({"label": "Revenue (normalized)", "data": _norm_series(d["revenue"])})
    if "purchases" in d.columns:
        norm_sets.append({"label": "Orders (normalized)", "data": _norm_series(d["purchases"])})
    if "active_users" in d.columns:
        norm_sets.append({"label": "Active buyers (normalized)", "data": _norm_series(d["active_users"])})
    if "line_items" in d.columns:
        norm_sets.append({"label": "Line items (normalized)", "data": _norm_series(d["line_items"])})
    if len(norm_sets) >= 2:
        chart_norm = json.dumps({"labels": labels, "datasets": norm_sets})

    return {
        "metric_label": metric.replace("_", " ").title(),
        "metric": metric,
        "csv_name": csv_path.name,
        "n_days": len(d),
        "n_anomalies": sum(anom),
        "summary_html": summary_html,
        "selected": sel,
        "selected_day_human": _human_date(str(sel.get("date"))),
        "pick_index": pick_i,
        "day_options": day_options,
        "chart_line": json.dumps(
            {
                "labels": labels,
                "values": values,
                "rolling": rolling,
                "anomalies": anom,
                "z": z_scores,
            }
        ),
        "chart_z": json.dumps({"labels": labels, "z": z_scores}),
        "chart_f1": json.dumps(f1_chart),
        "chart_pr": json.dumps(pr_chart),
        "chart_norm": chart_norm,
        "root_causes": sel.get("root_causes") or [],
        "ranked_actions": sel.get("ranked_actions") or [],
        "explanation": sel.get("explanation_text") or "",
        "report": report,
        "detection": detection,
        "focus_is_anomaly": bool(sel.get("is_anomaly")),
        "focus_confidence": sel.get("confidence"),
    }
