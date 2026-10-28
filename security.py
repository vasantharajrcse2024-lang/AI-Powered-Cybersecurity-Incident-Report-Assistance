"""Small local-app safeguards; not a replacement for deployment access control."""
from __future__ import annotations
import re

def validate_incident_id(value: str) -> str:
    value = value.strip()
    if not value or len(value) > 80 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
        raise ValueError("Incident ID must be 1–80 characters using letters, numbers, dot, underscore, or hyphen.")
    return value

def validate_reviewer(value: str) -> str:
    value = value.strip()
    if not value or len(value) > 100: raise ValueError("Enter a reviewer name (maximum 100 characters).")
    return value
