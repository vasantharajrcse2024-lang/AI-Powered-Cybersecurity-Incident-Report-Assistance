"""SQLite persistence layer with parameterized queries and minimal audit metadata."""
from __future__ import annotations
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.getenv("INCIDENT_DB_PATH", Path(__file__).resolve().parents[1] / "incident_reports.db"))

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def connect(path: str | Path | None = None) -> sqlite3.Connection:
    db = sqlite3.connect(str(path or DB_PATH), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db

def init_db(path: str | Path | None = None) -> None:
    with connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS incidents (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, reporting_period TEXT, description TEXT, created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Draft', category TEXT, severity TEXT);
        CREATE TABLE IF NOT EXISTS evidence (id TEXT PRIMARY KEY, incident_pk TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE, source_name TEXT NOT NULL, line_number INTEGER, text TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS indicators (id TEXT PRIMARY KEY, incident_pk TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE, type TEXT NOT NULL, value TEXT NOT NULL, evidence_ids TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS timeline_events (id TEXT PRIMARY KEY, incident_pk TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE, evidence_id TEXT NOT NULL, original_timestamp TEXT, normalized_timestamp TEXT, flag TEXT, text TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, incident_pk TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE, report_json TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE, reviewer TEXT NOT NULL, decision TEXT NOT NULL, note TEXT, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit_events (id TEXT PRIMARY KEY, incident_pk TEXT REFERENCES incidents(id) ON DELETE SET NULL, action TEXT NOT NULL, actor TEXT, details TEXT, created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_evidence_incident ON evidence(incident_pk);
        CREATE INDEX IF NOT EXISTS idx_reports_incident ON reports(incident_pk);
        """)

def create_incident(incident_id: str, period: str, description: str, evidence_records: list[dict], path=None) -> str:
    pk = str(uuid.uuid4()); created = now_utc()
    with connect(path) as db:
        db.execute("INSERT INTO incidents(id,incident_id,reporting_period,description,created_at) VALUES(?,?,?,?,?)", (pk, incident_id.strip(), period, description.strip(), created))
        for item in evidence_records:
            db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?)", (item["id"], pk, item.get("source_name", "pasted_notes.txt"), item.get("line_number"), item["text"], created))
        audit(db, pk, "incident_created", "local analyst", f"Evidence items: {len(evidence_records)}")
    return pk

def add_analysis(incident_pk: str, indicators: list[dict], timeline: list[dict], classification: dict, path=None) -> None:
    with connect(path) as db:
        db.execute("DELETE FROM indicators WHERE incident_pk=?", (incident_pk,)); db.execute("DELETE FROM timeline_events WHERE incident_pk=?", (incident_pk,))
        for item in indicators:
            db.execute("INSERT INTO indicators VALUES(?,?,?, ?,?)", (str(uuid.uuid4()), incident_pk, item["type"], item["value"], json.dumps(item["evidence_ids"])))
        for event in timeline:
            db.execute("INSERT INTO timeline_events VALUES(?,?,?,?,?,?,?)", (str(uuid.uuid4()), incident_pk, event["evidence_id"], event["original"], event["normalized"], event["flag"], event["text"]))
        db.execute("UPDATE incidents SET category=?,severity=? WHERE id=?", (classification["category"], classification["severity"], incident_pk))
        audit(db, incident_pk, "analysis_run", "local analyst", f"Category suggestion: {classification['category']}; severity: {classification['severity']}")

def save_report(incident_pk: str, report: dict, status: str = "Draft", path=None) -> str:
    report_id = str(uuid.uuid4()); timestamp = now_utc()
    with connect(path) as db:
        db.execute("INSERT INTO reports VALUES(?,?,?,?,?,?)", (report_id, incident_pk, json.dumps(report, ensure_ascii=False), status, timestamp, timestamp))
        audit(db, incident_pk, "report_generated", "local analyst", f"Report {report_id} saved as {status}")
    return report_id

def get_report(report_id: str, path=None) -> dict | None:
    with connect(path) as db:
        row = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
        if row:
            result = dict(row); result["report"] = json.loads(result.pop("report_json")); return result
    return None

def update_report(report_id: str, report: dict, status: str, path=None) -> None:
    timestamp = now_utc()
    with connect(path) as db:
        row = db.execute("SELECT incident_pk FROM reports WHERE id=?", (report_id,)).fetchone()
        if not row: raise KeyError("Report not found")
        db.execute("UPDATE reports SET report_json=?,status=?,updated_at=? WHERE id=?", (json.dumps(report, ensure_ascii=False), status, timestamp, report_id))
        audit(db, row["incident_pk"], "report_updated", "local analyst", f"Status changed to {status}")

def record_review(report_id: str, reviewer: str, decision: str, note: str = "", path=None) -> None:
    with connect(path) as db:
        db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?)", (str(uuid.uuid4()), report_id, reviewer.strip(), decision, note.strip(), now_utc()))

def audit(db: sqlite3.Connection, incident_pk: str | None, action: str, actor: str, details: str = "") -> None:
    db.execute("INSERT INTO audit_events VALUES(?,?,?,?,?,?)", (str(uuid.uuid4()), incident_pk, action, actor, details[:500], now_utc()))

def list_incidents(path=None) -> list[dict]:
    with connect(path) as db: return [dict(row) for row in db.execute("SELECT * FROM incidents ORDER BY created_at DESC")]

def get_incident(incident_pk: str, path=None) -> dict | None:
    with connect(path) as db:
        inc = db.execute("SELECT * FROM incidents WHERE id=?", (incident_pk,)).fetchone()
        if not inc: return None
        return {"incident": dict(inc), "evidence": [dict(x) for x in db.execute("SELECT * FROM evidence WHERE incident_pk=? ORDER BY created_at,line_number", (incident_pk,))], "indicators": [dict(x) for x in db.execute("SELECT * FROM indicators WHERE incident_pk=?", (incident_pk,))], "timeline": [dict(x) for x in db.execute("SELECT * FROM timeline_events WHERE incident_pk=?", (incident_pk,))], "reports": [dict(x) for x in db.execute("SELECT * FROM reports WHERE incident_pk=? ORDER BY created_at DESC", (incident_pk,))]}

def list_audit(path=None) -> list[dict]:
    with connect(path) as db: return [dict(row) for row in db.execute("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT 200")]

def delete_incident(incident_pk: str, path=None) -> None:
    with connect(path) as db: db.execute("DELETE FROM incidents WHERE id=?", (incident_pk,))
