"""Conservative timestamp extraction; naive timestamps are flagged, never silently localized."""
from __future__ import annotations
import re
from datetime import timezone
from dateutil import parser as date_parser

TIMESTAMP_RE = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?|\d{1,2}/\d{1,2}/\d{4}[ T]\d{1,2}:\d{2}(?::\d{2})?(?:\s?(?:UTC|GMT|[+-]\d{2}:?\d{2}))?)\b", re.I)

def extract_timestamp(text: str) -> dict:
    match = TIMESTAMP_RE.search(text)
    if not match:
        return {"original": None, "normalized": None, "flag": "Missing timestamp"}
    original = match.group(0)
    try:
        dt = date_parser.parse(original, fuzzy=False)
        if dt.tzinfo is None:
            # Date-only and timezone-naive event times are ambiguous; retain but do not invent zone.
            return {"original": original, "normalized": None, "flag": "Timezone missing; UTC conversion unavailable"}
        normalized = dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        return {"original": original, "normalized": normalized, "flag": None}
    except (ValueError, OverflowError):
        return {"original": original, "normalized": None, "flag": "Unparseable or ambiguous timestamp"}

def build_timeline(evidence: list[dict]) -> list[dict]:
    events = []
    for item in evidence:
        ts = extract_timestamp(item.get("text", ""))
        events.append({"evidence_id": item["id"], "source_name": item.get("source_name", ""), "text": item.get("text", ""), **ts})
    # Sort only known normalized timestamps; unknowns remain afterward in evidence order.
    return sorted(events, key=lambda e: (e["normalized"] is None, e["normalized"] or "", e["evidence_id"]))
