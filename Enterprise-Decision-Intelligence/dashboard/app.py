"""Streamlit dashboard: pipeline + RCA + decision + evaluation."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from enterprise_decision_intel.config import detection_sensitivity
from enterprise_decision_intel.data_pipeline import load_ga4_style_csv
from enterprise_decision_intel.evaluation.runner import evaluation_table, run_advanced_evaluation, run_evaluation
from enterprise_decision_intel.pipeline import run_dataset_from_df


def _day_labels(traces: list[dict]) -> list[str]:
    out: list[str] = []
    for t in traces:
        d = t.get("date") or ""
        try:
            human = pd.Timestamp(d).strftime("%b %d, %Y")
        except Exception:
            human = str(d)[:10]
        tag = "Anomaly" if t.get("is_anomaly") else "Normal"
        out.append(f"{human} · {tag}")
    return out


def _default_day_index(traces: list[dict]) -> int:
    anom = [i for i, t in enumerate(traces) if t.get("is_anomaly")]
    if anom:
        return anom[-1]
    return max(0, len(traces) - 1)


def _list_data_csvs() -> list[Path]:
    data_dir = PROJECT_ROOT / "data"
    return sorted(data_dir.glob("*.csv"))


def main() -> None:
    st.set_page_config(page_title="Enterprise Decision Intelligence", layout="wide")
    st.title("Enterprise Decision Intelligence Dashboard")
    with st.sidebar:
        csv_files = _list_data_csvs()
        default_path = PROJECT_ROOT / "data" / "ga4_public_daily.csv"
        options = [str(p) for p in csv_files] or [str(default_path)]
        selected_csv = st.selectbox("Dataset", options, index=0)
        metric = st.selectbox("KPI", ["revenue", "conversion_rate", "churn", "cac"], index=0)
        window = st.slider("Rolling window", 7, 28, 14)
        run_eval = st.checkbox("Run evaluation", value=True)
        runs = st.slider("Advanced runs", 3, 5, 3)
        seed = st.number_input("Seed", value=42, step=1)
        human_approved = st.checkbox(
            "Human approved (execute ranked actions)",
            value=False,
            help="Clears pending_human_approval when anomalies fire: simulates sign-off on recommendations.",
        )
        sensitivity_key = st.selectbox(
            "Anomaly sensitivity (real data only)",
            options=["standard", "balanced", "sensitive", "explorer"],
            index=1,
            format_func=lambda k: {
                "standard": "Standard (z≥2.5, stricter)",
                "balanced": "Balanced (z≥2.0)",
                "sensitive": "Sensitive (z≥1.7)",
                "explorer": "Explorer (z≥1.45, most flags)",
            }[k],
            help="Same CSV: lower z-threshold flags more genuine statistical outliers. No synthetic spikes.",
        )

    csv_path = Path(selected_csv)
    if not csv_path.is_file():
        st.error(f"Dataset not found: {csv_path}")
        return

    df = load_ga4_style_csv(csv_path)
    if metric not in df.columns:
        st.error(f"Metric `{metric}` not present in dataset")
        return

    detection_cfg = detection_sensitivity(sensitivity_key)
    result = run_dataset_from_df(
        df,
        metric_col=metric,
        rolling_window=window,
        human_approved=human_approved,
        detection=detection_cfg,
    )
    traces = result.rows
    if not traces:
        st.warning("No pipeline output.")
        return

    labels = _day_labels(traces)
    default_i = _default_day_index(traces)
    with st.sidebar:
        st.divider()
        day_idx = st.selectbox(
            "Inspect day",
            range(len(traces)),
            index=min(default_i, len(traces) - 1),
            format_func=lambda i: labels[i],
            help="Pick any date to view anomaly score, RCA, actions, and explanation for that day.",
        )
    focus = traces[int(day_idx)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", len(df))
    c2.metric("Anomaly days", sum(1 for t in traces if t.get("is_anomaly")))
    c3.metric("Score (selected day)", f"{float(focus.get('anomaly_score') or 0.0):.3f}")
    c4.metric("Confidence (selected day)", f"{float(focus.get('confidence') or 0.0):.3f}")

    st.subheader("Time-series")
    fig, ax = plt.subplots(figsize=(12, 4))
    x = pd.to_datetime(df["date"])
    y = pd.to_numeric(df[metric], errors="coerce")
    ax.plot(x, y, label=metric, color="tab:blue")
    anomaly_dates = [pd.Timestamp(t["date"]) for t in traces if t.get("is_anomaly")]
    if anomaly_dates:
        mask = x.isin(anomaly_dates)
        ax.scatter(x[mask], y[mask], color="tab:red", label="anomaly", zorder=3)
    ax.legend()
    ax.set_xlabel("date")
    ax.set_ylabel(metric)
    st.pyplot(fig, clear_figure=True)

    st.subheader("Anomaly + Root Cause + Decision")
    st.write(f"Anomaly detected: **{bool(focus.get('is_anomaly'))}**")
    st.write(f"Execution status: **{focus.get('execution_status', 'not_requested')}**")

    rc = pd.DataFrame(focus.get("root_causes_ranked") or [])
    st.markdown("**Root causes (%)**")
    st.dataframe(rc, width="stretch", hide_index=True)

    ra = pd.DataFrame(focus.get("ranked_actions") or [])
    st.markdown("**Decision recommendations**")
    st.dataframe(ra, width="stretch", hide_index=True)

    st.markdown("**Explanation**")
    st.text(focus.get("explanation_text", ""))

    if run_eval:
        st.subheader("Evaluation")
        st.caption(
            "Injected anomalies update revenue and drivers; **cac / churn / conversion_rate are recomputed** "
            "so labels match the selected KPI. Cohen’s κ stays empty unless the CSV has two human label columns."
        )
        report = run_evaluation(df, mode="inject", metric_col=metric, rolling_window=window, seed=int(seed))
        comp = evaluation_table(report)
        st.dataframe(comp, width="stretch", hide_index=True)

        adv = run_advanced_evaluation(df, metric_col=metric, runs=runs, base_seed=int(seed))
        st.markdown("**Advanced evaluation**")
        st.json(
            {
                "paired_t_test_agent_vs_baseline2": adv["paired_t_test_agent_vs_baseline2"],
                "cohens_kappa_explanation": adv["cohens_kappa_explanation"],
                "seeds": adv["seeds"],
            }
        )


if __name__ == "__main__":
    main()
