from __future__ import annotations

from datetime import datetime
from typing import Any

from enterprise_decision_intel.shared_memory import SharedMemory


def _fmt_num(x: Any) -> str:
    if x is None:
        return "—"
    try:
        v = float(x)
        if abs(v) >= 1000:
            return f"{v:,.2f}"
        return f"{v:.2f}"
    except (TypeError, ValueError):
        return str(x)


def _fmt_day(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return iso[:10]


class ExplanationAgent:
    """Structured narrative from computed stats only (no external API)."""

    def run(self, state: SharedMemory) -> SharedMemory:
        state.explanation_text = self._template_explain(_payload_from_state(state)).strip()
        return state

    def _template_explain(self, payload: dict[str, Any]) -> str:
        m = payload["metric_name"].replace("_", " ")
        day = _fmt_day(payload.get("timestamp"))
        lines = [
            f"{m.title()} · {day}: value {_fmt_num(payload['current_value'])}, "
            f"baseline {_fmt_num(payload['rolling_mean'])}, spread {_fmt_num(payload['rolling_std'])}.",
        ]
        if payload.get("is_anomaly"):
            lines.append(
                f"Anomaly score {_fmt_num(payload['anomaly_score'])} · confidence {_fmt_num(payload['confidence'])}."
            )
        else:
            lines.append("Within expected variation for this window — no root-cause pass on this day.")
        rc = payload.get("root_causes") or []
        if rc:
            top = ", ".join(f"{r['dimension']}={r['value']} ({r['contribution_pct']}%)" for r in rc[:5])
            lines.append(f"Top dimensional shifts: {top}.")
        acts = payload.get("ranked_actions") or []
        if acts:
            why = acts[0].get("why_ranked") or ""
            tail = f" — {why}" if why else ""
            lines.append(
                f"Top action: {acts[0]['label']} (utility {acts[0]['utility']:.2f}){tail}"
                + (f"; next: {acts[1]['label']}" if len(acts) > 1 else "")
                + "."
            )
        if payload.get("flagged_for_review"):
            lines.append("Flagged for human review (low confidence or missing baseline).")
        return "\n".join(lines)


def _payload_from_state(state: SharedMemory) -> dict[str, Any]:
    return {
        "timestamp": state.timestamp.isoformat() if state.timestamp else None,
        "metric_name": state.metric_name,
        "current_value": state.current_value,
        "rolling_mean": state.rolling_mean,
        "rolling_std": state.rolling_std,
        "ewma_value": state.ewma_value,
        "anomaly_score": state.anomaly_score,
        "confidence": state.confidence,
        "is_anomaly": state.is_anomaly,
        "flagged_for_review": state.flagged_for_review,
        "root_causes": state.root_causes,
        "ranked_actions": state.ranked_actions,
        "controller_notes": state.controller_notes,
    }
