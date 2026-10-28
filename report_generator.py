"""Structured report generation from evidence; claims are bounded to observed records."""
from __future__ import annotations
from datetime import datetime, timezone

def generate_report(incident: dict, evidence: list[dict], timeline: list[dict], indicators: list[dict], classification: dict) -> dict:
    refs = lambda ids: [f"E-{i}" for i in ids]
    observed = [{"claim": f"Evidence item E-{e['id']} records: {e['text']}", "evidence_ids": [e["id"]], "kind": "Observed fact"} for e in evidence]
    time_rows = [{"evidence_id": e["evidence_id"], "original_timestamp": e["original"], "normalized_utc": e["normalized"], "flag": e["flag"], "event_text": e["text"]} for e in timeline]
    unknowns = []
    if not any(e["normalized"] for e in timeline): unknowns.append("No timezone-aware timestamps were available; chronology cannot be reliably established.")
    elif any(e["flag"] for e in timeline): unknowns.append("Some evidence timestamps are missing, timezone-naive, or ambiguous.")
    if not evidence: unknowns.append("No evidence items were supplied.")
    assets = [x["value"] for x in indicators if x["type"] == "Hostname"]
    return {
        "incident_id": incident["incident_id"], "reporting_period": incident.get("reporting_period") or "Not specified",
        "executive_summary": {"text": "This is a draft, evidence-bounded summary. " + (f"The submitted evidence matches configured rules for {classification['category']} (suggested severity: {classification['severity']})." if evidence else "No evidence was available to support a summary."), "evidence_ids": sorted({i for e in observed for i in e["evidence_ids"]}), "status": "AI-assisted draft; analyst review required"},
        "classification": {**classification, "label": "Suggested, not confirmed"}, "affected_assets": [{"value": x, "evidence_ids": sorted({i for row in indicators if row["type"] == "Hostname" and row["value"] == x for i in row["evidence_ids"]})} for x in sorted(set(assets))] or [{"value": "Not supported by available evidence", "evidence_ids": []}],
        "timeline": time_rows,
        "observed_indicators": [{"type": i["type"], "value": i["value"], "status": i["status"], "evidence_ids": i["evidence_ids"]} for i in indicators],
        "potential_impact": {"text": "Not assessed; requires analyst validation.", "evidence_ids": []}, "confirmed_impact": {"text": "Not supported by available evidence.", "evidence_ids": []},
        "response_actions_completed": {"text": "Not supported by available evidence.", "evidence_ids": []},
        "recommended_follow_up": ["Validate timestamps and affected scope with the incident owner.", "Preserve original evidence and document any containment or recovery actions actually performed.", "Have an authorized analyst review each claim before approval."],
        "unknowns_and_evidence_gaps": unknowns or ["No specific evidence gaps were detected by this basic rule-based workflow; analyst review is still required."],
        "lessons_learned": "Not assessed; complete after incident review.", "evidence_claims": observed,
        "review": {"status": "Draft", "reviewer": None, "approved_at": None},
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"), "generation_note": "Rule-based draft; not an AI-confirmed assessment. Unsupported information is explicitly marked."
    }
