import json
from pathlib import Path
from incident_assistant.ingestion import parse_evidence, IntakeError
from incident_assistant.timeline import extract_timestamp, build_timeline
from incident_assistant.indicators import extract_indicators
from incident_assistant.classification import classify
from incident_assistant.report_generator import generate_report
from incident_assistant.export_utils import report_json, report_text
from incident_assistant.ai_adapter import AIAdapter
from incident_assistant.database import init_db, create_incident, add_analysis, save_report, get_report, list_incidents, delete_incident

def test_ingestion_txt_json_csv_and_validation():
    assert len(parse_evidence("x.txt", b"one\ntwo")) == 2
    assert parse_evidence("x.json", b'{"event":"login"}')[0]["text"].startswith('{')
    assert "source" in parse_evidence("x.csv", b"source,event\nhost,login")[0]["text"]
    for name, data in [("x.exe", b"x"), ("x.json", b"{")]:
        try: parse_evidence(name, data); assert False
        except IntakeError: pass
    try: parse_evidence("large.txt", b"12345", max_bytes=4); assert False
    except IntakeError: pass

def test_timestamp_normalization_and_flags():
    assert extract_timestamp("2026-10-28T13:00:00+05:30 event")["normalized"] == "2026-10-28T07:30:00Z"
    assert extract_timestamp("2026-10-28 13:00 login")["normalized"] is None
    assert extract_timestamp("no time here")["flag"] == "Missing timestamp"

def test_indicators_classification_and_linking():
    evidence=[{"id":"E-001","text":"2026-10-28T09:00:00Z phishing alert from 198.51.100.7 host=WS-01 event id: 4625"}]
    inds=extract_indicators(evidence); assert any(x["value"]=="198.51.100.7" for x in inds)
    result=classify(evidence); assert result["category"]=="Phishing" and "E-001" in result["evidence_ids"]
    report=generate_report({"incident_id":"IR-1","reporting_period":"today"},evidence,build_timeline(evidence),inds,result)
    assert report["evidence_claims"][0]["evidence_ids"]==["E-001"]
    assert report["confirmed_impact"]["text"]=="Not supported by available evidence."

def test_fallback_exports_and_database(tmp_path):
    evidence=[{"id":"E-001","text":"suspicious login from 203.0.113.9"}]
    assert AIAdapter().analyze(evidence)["generation_mode"]=="rule-based fallback"
    result=classify(evidence); timeline=build_timeline(evidence); indicators=extract_indicators(evidence)
    report=generate_report({"incident_id":"IR-T","reporting_period":"test"},evidence,timeline,indicators,result)
    assert b"DRAFT" in report_json(report,"Draft") and "DRAFT" in report_text(report,"Draft")
    path=tmp_path/"test.db"; init_db(path)
    pk=create_incident("IR-T","test","",evidence,path); add_analysis(pk,indicators,timeline,result,path)
    rid=save_report(pk,report,path=path); assert get_report(rid,path)["status"]=="Draft"
    assert len(list_incidents(path))==1; delete_incident(pk,path); assert list_incidents(path)==[]
