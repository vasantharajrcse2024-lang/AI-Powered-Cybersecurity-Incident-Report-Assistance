"""Explainable category/severity suggestions; outputs are not confirmed findings."""
from __future__ import annotations

RULES = [
    ("Phishing", ["phishing", "suspicious email", "credential harvest", "malicious link"]),
    ("Malware", ["malware", "ransomware", "trojan", "quarantined file", "malicious file"]),
    ("Suspicious login", ["failed login", "impossible travel", "unauthorized login", "multiple login", "authentication failure"]),
    ("Denial of service", ["denial of service", "ddos", "traffic flood", "service unavailable"]),
]

def classify(evidence: list[dict]) -> dict:
    corpus = "\n".join(x.get("text", "") for x in evidence).lower()
    matched = [(name, [term for term in terms if term in corpus]) for name, terms in RULES]
    matched = [(name, terms) for name, terms in matched if terms]
    if not matched:
        return {"category": "Unclassified", "severity": "Low", "confidence": "Low", "rationale": "No configured classification phrase was found in the submitted evidence. This is not evidence that no incident occurred.", "evidence_ids": []}
    category, terms = matched[0]
    ids = [item["id"] for item in evidence if any(t in item.get("text", "").lower() for t in terms)]
    high_terms = ["ransomware", "data exfiltration", "domain admin", "widespread", "critical system", "ddos"]
    medium_terms = ["malware", "phishing", "unauthorized login", "suspicious login", "credential harvest"]
    severity = "High" if any(t in corpus for t in high_terms) else ("Medium" if any(t in corpus for t in medium_terms) else "Low")
    confidence = "Medium" if len(set(terms)) > 1 or len(ids) > 1 else "Low"
    return {"category": category, "severity": severity, "confidence": confidence, "rationale": f"Configured keyword rules matched: {', '.join(terms)}. Severity is a suggested rubric result, not a confirmed impact assessment.", "evidence_ids": sorted(set(ids))}
