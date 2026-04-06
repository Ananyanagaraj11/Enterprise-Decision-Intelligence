from __future__ import annotations

import json
import os
from urllib import request
from datetime import datetime
from typing import Any

from enterprise_decision_intel.config import DetectionConfig
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
    """Structured narrative from computed stats; optional LLM API if configured."""

    def run(self, state: SharedMemory) -> SharedMemory:
        payload = _payload_from_state(state)
        state.explanation_text = self._llm_or_template_explain(payload).strip()
        return state

    def _llm_or_template_explain(self, payload: dict[str, Any]) -> str:
        endpoint = os.getenv("LLM_API_ENDPOINT", "").strip()
        api_key = os.getenv("LLM_API_KEY", "").strip()
        model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
        if not endpoint or not api_key:
            return self._template_explain(payload)
        try:
            prompt = (
                "You are an enterprise analytics explanation assistant.\n"
                "Use ONLY values present in the JSON payload. Do NOT invent numbers.\n"
                "Return exactly three sections in plain text:\n"
                "1) What happened\n2) Why it happened\n3) What to do\n\n"
                f"Payload:\n{json.dumps(payload, ensure_ascii=True)}"
            )
            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Use only provided computed values."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
            }
            req = request.Request(
                endpoint,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with request.urlopen(req, timeout=20) as resp:
                out = json.loads(resp.read().decode("utf-8"))
            text = (
                out.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return text or self._template_explain(payload)
        except Exception:
            return self._template_explain(payload)

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
        if payload.get("execution_status") == "pending_human_approval":
            lines.append("Awaiting human approval before executing ranked actions.")
        elif payload.get("execution_status") == "approved_for_execution":
            lines.append("Human approval recorded; ranked actions are cleared for execution in this simulation.")
        min_conf = float(
            payload.get("min_confidence")
            if payload.get("min_confidence") is not None
            else DetectionConfig().min_confidence
        )
        conf = payload.get("confidence")
        if payload.get("flagged_for_review") and (
            conf is None or float(conf or 0.0) < min_conf
        ):
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
        "execution_status": state.execution_status,
        "min_confidence": DetectionConfig().min_confidence,
        "root_causes": state.root_causes,
        "ranked_actions": state.ranked_actions,
        "controller_notes": state.controller_notes,
    }
