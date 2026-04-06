"""Interactive dashboard: GA4 metrics, anomalies, baselines, evaluation (Streamlit)."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from enterprise_decision_intel.config import DetectionConfig
from enterprise_decision_intel.data_pipeline import load_ga4_style_csv
from enterprise_decision_intel.evaluation.injection import inject_controlled_anomalies
from enterprise_decision_intel.evaluation.runner import run_evaluation
from enterprise_decision_intel.pipeline import run_dataset_from_df


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            @keyframes ediFadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes ediPulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.85; }
            }
            .main .block-container {
                padding-top: 1.25rem;
                max-width: 1200px;
            }
            div[data-testid="stMetricValue"] {
                font-variant-numeric: tabular-nums;
            }
            .hero-title {
                font-size: 1.85rem;
                font-weight: 700;
                letter-spacing: -0.03em;
                color: #0f172a;
                margin-bottom: 0.15rem;
                animation: ediFadeIn 0.55s ease-out;
            }
            .hero-sub {
                color: #64748b;
                font-size: 0.95rem;
                margin-bottom: 1.25rem;
                animation: ediFadeIn 0.65s ease-out;
            }
            .card {
                background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                padding: 1rem 1.15rem;
                box-shadow: 0 1px 3px rgba(15,23,42,0.06);
                animation: ediFadeIn 0.7s ease-out;
            }
            .badge {
                display: inline-block;
                padding: 0.2rem 0.55rem;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 600;
                letter-spacing: 0.02em;
            }
            .badge-anom { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
            .badge-ok { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
            .hint { color: #64748b; font-size: 0.88rem; line-height: 1.45; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def human_day(trace_date: str | None) -> str:
    if not trace_date:
        return "—"
    try:
        return pd.Timestamp(trace_date).strftime("%b %d, %Y")
    except Exception:
        return str(trace_date)[:10]


def default_day_index(traces: list[dict]) -> int:
    anom = [i for i, t in enumerate(traces) if t.get("is_anomaly")]
    if anom:
        return anom[-1]
    return max(0, len(traces) - 1)


def rolling_stats(s: pd.Series, window: int) -> tuple[pd.Series, pd.Series]:
    cfg = DetectionConfig(rolling_window=window)
    rm = s.rolling(cfg.rolling_window, min_periods=max(3, cfg.rolling_window // 2)).mean()
    rstd = s.rolling(cfg.rolling_window, min_periods=max(3, cfg.rolling_window // 2)).std()
    return rm, rstd


def fig_timeseries(df: pd.DataFrame, traces: list[dict], metric: str, window: int) -> go.Figure:
    d = df.sort_values("date").reset_index(drop=True)
    dates = pd.to_datetime(d["date"])
    y = d[metric].astype(float)
    rm, _ = rolling_stats(y, window)
    anom_dates = [pd.Timestamp(t["date"]) for t in traces if t.get("is_anomaly")]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=y,
            name=metric.replace("_", " ").title(),
            line=dict(color="#4f46e5", width=2.2),
            hovertemplate="%{x|%b %d, %Y}<br>%{y:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=rm,
            name=f"Rolling mean ({window}d)",
            line=dict(color="#94a3b8", width=1.8, dash="dash"),
            hovertemplate="%{x|%b %d, %Y}<br>%{y:,.2f}<extra></extra>",
        )
    )
    if len(anom_dates):
        mask = dates.isin(anom_dates)
        fig.add_trace(
            go.Scatter(
                x=dates[mask],
                y=y[mask],
                mode="markers",
                name="Anomaly",
                marker=dict(size=12, color="#dc2626", symbol="circle", line=dict(width=2, color="#fff")),
                hovertemplate="%{x|%b %d, %Y}<br>Anomaly<br>%{y:,.2f}<extra></extra>",
            )
        )
    fig.update_layout(
        template="plotly_white",
        height=440,
        margin=dict(l=16, r=16, t=48, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fafafa",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor="#e8e8e8"),
        yaxis=dict(showgrid=True, gridcolor="#e8e8e8"),
        title=dict(text=f"{metric.replace('_', ' ').title()} over time", font=dict(size=16, color="#0f172a")),
        transition=dict(duration=350, easing="cubic-in-out"),
    )
    return fig


def fig_detection_bars(detection: dict) -> go.Figure:
    rows = []
    for name, key in [
        ("Agentic", "agentic_system"),
        ("B1 · Static", "baseline_1_static_threshold"),
        ("B2 · Z-only", "baseline_2_z_only"),
        ("B3 · Manual", "baseline_3_manual_script"),
    ]:
        m = detection.get(key) or {}
        rows.append(
            dict(model=name, precision=m.get("precision", 0), recall=m.get("recall", 0), f1=m.get("f1", 0))
        )
    dd = pd.DataFrame(rows)
    fig = go.Figure()
    for col, color in [("precision", "#6366f1"), ("recall", "#0ea5e9"), ("f1", "#16a34a")]:
        fig.add_trace(go.Bar(name=col.title(), x=dd["model"], y=dd[col], marker_color=color))
    fig.update_layout(
        barmode="group",
        template="plotly_white",
        height=400,
        margin=dict(l=16, r=16, t=40, b=72),
        xaxis_tickangle=-18,
        yaxis_range=[0, 1.05],
        legend=dict(orientation="h", y=1.12),
        title=dict(text="Detection quality vs baselines", font=dict(size=15)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fafafa",
        transition=dict(duration=400, easing="cubic-in-out"),
    )
    return fig


def fig_f1_only(detection: dict) -> go.Figure:
    names = ["Agent", "B1", "B2", "B3"]
    keys = [
        "agentic_system",
        "baseline_1_static_threshold",
        "baseline_2_z_only",
        "baseline_3_manual_script",
    ]
    f1s = [(detection.get(k) or {}).get("f1", 0) for k in keys]
    colors = ["#16a34a", "#cbd5e1", "#cbd5e1", "#cbd5e1"]
    fig = go.Figure(
        go.Bar(
            x=names,
            y=f1s,
            marker_color=colors,
            text=[f"{v:.2f}" for v in f1s],
            textposition="outside",
        )
    )
    fig.update_layout(
        template="plotly_white",
        height=300,
        yaxis_range=[0, 1.05],
        title=dict(text="F1 score (detection)", font=dict(size=14)),
        margin=dict(l=16, r=16, t=48, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fafafa",
        showlegend=False,
        transition=dict(duration=400, easing="cubic-in-out"),
    )
    return fig


def main() -> None:
    inject_styles()

    st.markdown('<p class="hero-title">Enterprise Decision Intelligence</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-sub">GA4 sample data · monitoring → anomaly detection → attribution → ranked actions</p>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### Data")
        default_csv = PROJECT_ROOT / "data" / "ga4_public_daily.csv"
        csv_str = st.text_input("CSV path", value=str(default_csv), label_visibility="collapsed")
        st.caption("CSV path")
        metric = st.selectbox("Metric", ["revenue", "sessions", "purchases", "conversion_rate"], index=0)
        window = st.slider("Rolling window (days)", 7, 28, 14)
        st.divider()
        st.markdown("### Evaluation")
        run_eval = st.checkbox("Inject + evaluate (report tab)", value=True)
        inject_n = st.number_input("Injected events", min_value=3, max_value=25, value=8, step=1)
        seed = st.number_input("Random seed", value=42, step=1)

    csv_path = Path(csv_str)
    if not csv_path.is_file():
        st.error(f"File not found: {csv_path}")
        st.info("Export: `python scripts/fetch_ga4_bigquery.py --out data/ga4_public_daily.csv`")
        return

    df = load_ga4_style_csv(csv_path)
    if metric not in df.columns:
        st.error(f"Column `{metric}` not in CSV.")
        return

    report: dict | None = None
    traces: list[dict] = []

    if run_eval:
        try:
            inj = inject_controlled_anomalies(df, int(inject_n), seed=int(seed))
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
        except Exception as e:
            st.warning(f"Evaluation failed ({e}). Showing raw series.")
            report = None
            result = run_dataset_from_df(df, metric_col=metric, rolling_window=window)
            traces = result.rows
            df_plot = df
    else:
        result = run_dataset_from_df(df, metric_col=metric, rolling_window=window)
        traces = result.rows
        df_plot = df

    tab1, tab2, tab3 = st.tabs(["Overview", "Time series & RCA", "Evaluation"])

    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        n_days = len(df_plot)
        n_anom = sum(1 for t in traces if t.get("is_anomaly"))
        last = traces[-1] if traces else {}
        c1.metric("Days", f"{n_days:,}")
        c2.metric("Anomaly days", f"{n_anom}")
        c3.metric("Last z-score", f"{last.get('anomaly_score') or 0:.2f}")
        c4.metric("Confidence", f"{last.get('confidence') or 0:.2f}")
        with st.expander("Latest raw trace (JSON)", expanded=False):
            st.json(last if last else {})

    with tab2:
        st.plotly_chart(fig_timeseries(df_plot, traces, metric, window), use_container_width=True)

        st.markdown("### Pick a day")
        if not traces:
            st.warning("No traces to inspect.")
            sel = {}
        else:
            idx_default = default_day_index(traces)
            labels = []
            for t in traces:
                dstr = human_day(str(t.get("date")))
                if t.get("is_anomaly"):
                    labels.append(f"{dstr}  ·  Anomaly")
                else:
                    labels.append(f"{dstr}  ·  Normal")

            pick_i = st.selectbox(
                "Date",
                range(len(traces)),
                index=min(idx_default, len(traces) - 1),
                format_func=lambda i: labels[i],
                help="Defaults to the latest day flagged as an anomaly (if any).",
            )
            sel = traces[pick_i]

        st.markdown("### Narrative")
        nar_raw = (sel.get("explanation_text") or last.get("explanation_text") or "—") if traces else "—"
        nar_safe = html.escape(nar_raw).replace("\n", "<br/>")
        st.markdown(f'<div class="card"><span class="hint">{nar_safe}</span></div>', unsafe_allow_html=True)

        st.markdown("### Root causes & ranked actions")
        is_anom = bool(sel.get("is_anomaly"))
        badge = (
            '<span class="badge badge-anom">Anomaly</span>'
            if is_anom
            else '<span class="badge badge-ok">Normal</span>'
        )
        st.markdown(
            f'<p style="margin:0.5rem 0 1rem 0;">{badge} <span class="hint">· {human_day(str(sel.get("date")))}</span></p>',
            unsafe_allow_html=True,
        )

        rc_df = pd.DataFrame(sel.get("root_causes") or [])
        act_df = pd.DataFrame(sel.get("ranked_actions") or [])

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Root causes**")
            if not is_anom:
                st.info(
                    "No root-cause table on **normal** days — the pipeline only attributes dimensions "
                    "after an anomaly is confirmed (see proposal: confidence-gated stages)."
                )
            elif sel.get("flagged_for_review"):
                st.warning("Flagged for review (low confidence). Root cause may be withheld.")
            elif rc_df.empty:
                st.warning("Anomaly without attribution rows — often missing dimension baselines for this day.")
            else:
                st.dataframe(rc_df, use_container_width=True, hide_index=True)
        with c2:
            st.markdown("**Ranked actions**")
            if not is_anom:
                st.info("Ranked actions appear when an anomaly clears the gate — pick an **Anomaly** day above.")
            elif act_df.empty:
                st.warning("No actions returned for this day (check controller / confidence).")
            else:
                show = act_df.copy()
                if "utility" in show.columns:
                    show["utility"] = show["utility"].round(4)
                st.dataframe(show, use_container_width=True, hide_index=True)

    with tab3:
        if report:
            st.plotly_chart(fig_detection_bars(report.get("detection", {})), use_container_width=True)
            st.plotly_chart(fig_f1_only(report.get("detection", {})), use_container_width=True)
            d1, d2 = st.columns(2)
            with d1:
                st.markdown("**Root cause (top-k)**")
                st.json(report.get("root_cause", {}))
            with d2:
                st.markdown("**Decision & utility**")
                st.json(report.get("decision", {}))
            st.markdown("**System timing**")
            st.json(report.get("system", {}))
            with st.expander("Full report JSON"):
                st.code(json.dumps(report, indent=2), language="json")
        else:
            st.info("Turn on **Inject + evaluate** in the sidebar for baseline comparison charts.")


if __name__ == "__main__":
    main()
