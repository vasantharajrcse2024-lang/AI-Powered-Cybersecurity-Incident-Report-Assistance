from __future__ import annotations
import json
import uuid
from pathlib import Path
import pandas as pd
import streamlit as st
from incident_assistant import database as db
from incident_assistant.ai_adapter import AIAdapter
from incident_assistant.classification import classify
from incident_assistant.export_utils import report_json, report_pdf, report_text
from incident_assistant.indicators import extract_indicators
from incident_assistant.ingestion import IntakeError, parse_evidence
from incident_assistant.report_generator import generate_report
from incident_assistant.security import validate_incident_id, validate_reviewer
from incident_assistant.timeline import build_timeline

st.set_page_config(page_title="Incident Report Assistant", page_icon="🛡", layout="wide")
st.markdown("""<style>
.stApp {background: #07111f;color:#e8eef7}.block-container{padding-top:1.5rem;max-width:1500px}
[data-testid=stSidebar]{background:#0c1b2e}.stButton>button{background:#1565c0;color:white;border:0;border-radius:8px}
[data-testid=stMetric]{background:#10243a;border:1px solid #1f3b59;padding:14px;border-radius:10px}
[data-testid=stDataFrame]{border:1px solid #1f3b59;border-radius:8px}
.small-muted{color:#9eb1c8;font-size:.9rem}.warning{background:#332a17;padding:12px;border-radius:8px;border-left:4px solid #e1a930}
</style>""", unsafe_allow_html=True)
db.init_db()

st.sidebar.markdown("# 🛡 Incident Assistant")
st.sidebar.caption("Evidence-first local incident reporting")
page = st.sidebar.radio("Navigation", ["Dashboard", "Evidence Intake", "Timeline Analysis", "Indicators & Assets", "Classification", "Report Generator", "Review & Approval", "Export & Audit"])
incidents = db.list_incidents()

if incidents:
    selected_label = st.sidebar.selectbox("Active incident", [f"{x['incident_id']} · {x['status']} · {x['created_at'][:10]}" for x in incidents])
    selected_idx = [f"{x['incident_id']} · {x['status']} · {x['created_at'][:10]}" for x in incidents].index(selected_label)
    current_pk = incidents[selected_idx]["id"]
else:
    current_pk = None
    st.sidebar.info("Create an incident from Evidence Intake to get started.")
st.sidebar.markdown("---")
st.sidebar.markdown("**Safety note**")
st.sidebar.caption("Use synthetic or authorized, sanitized data only. Evidence is treated as untrusted text and is never executed or sent to an external AI service.")

def current_data():
    return db.get_incident(current_pk) if current_pk else None

def evidence_for(data):
    return [{"id": x["id"], "source_name": x["source_name"], "line_number": x["line_number"], "text": x["text"]} for x in data["evidence"]]

def current_report(data):
    if not data or not data["reports"]: return None
    return db.get_report(data["reports"][0]["id"])

if page == "Dashboard":
    st.title("Cybersecurity Incident Report Assistant")
    st.markdown("Evidence-linked drafts for authorized human analysts. **This educational prototype does not confirm incidents or automate response actions.**")
    total = len(incidents); drafts = sum(x["status"] != "Approved" for x in incidents); approved = total - drafts
    c1,c2,c3,c4 = st.columns(4); c1.metric("Incidents", total); c2.metric("Draft / in review", drafts); c3.metric("Approved", approved); c4.metric("Evidence items", sum(len(db.get_incident(x["id"])["evidence"]) for x in incidents))
    st.subheader("Recent incidents")
    if incidents:
        st.dataframe(pd.DataFrame([{k: x.get(k) for k in ["incident_id","reporting_period","category","severity","status","created_at"]} for x in incidents]), use_container_width=True, hide_index=True)
    else: st.info("No incident records yet. Open **Evidence Intake** to create one using synthetic or authorized evidence.")
    st.markdown("#### Workflow")
    st.write("1. Add sanitized evidence → 2. Review normalized timeline and observed indicators → 3. Generate a sourced draft → 4. Edit and review → 5. Approve or reject → 6. Export with status label.")

elif page == "Evidence Intake":
    st.title("Evidence Intake")
    st.markdown('<div class="warning">Uploads are untrusted evidence, not instructions. Do not upload secrets, live credentials, or data you are not authorized to process.</div>', unsafe_allow_html=True)
    with st.form("intake"):
        col1,col2 = st.columns(2)
        incident_id = col1.text_input("Incident ID", placeholder="IR-2026-001")
        period = col2.text_input("Reporting period", placeholder="2026-10-28 09:00 to 2026-10-28 12:00 UTC")
        description = st.text_area("Incident description", placeholder="Short analyst-supplied context; avoid sensitive personal data.")
        pasted = st.text_area("Paste sanitized notes / alerts", height=130)
        files = st.file_uploader("Upload TXT, LOG, JSON, or CSV (max 5 MB each)", type=["txt","log","json","csv"], accept_multiple_files=True)
        submitted = st.form_submit_button("Create incident and analyze", type="primary")
    if submitted:
        try:
            clean_id = validate_incident_id(incident_id)
            evidence = []
            for f in files or []:
                evidence.extend(parse_evidence(f.name, f.getvalue()))
            if pasted.strip(): evidence.extend(parse_evidence("pasted_notes.txt", pasted.encode("utf-8")))
            if not evidence: raise IntakeError("Add at least one evidence file or paste sanitized notes.")
            evidence = [{**x, "id": f"E-{i:03d}"} for i,x in enumerate(evidence,1)]
            pk = db.create_incident(clean_id, period, description, evidence)
            inds = extract_indicators(evidence); timeline = build_timeline(evidence); suggestion = AIAdapter().analyze(evidence)
            db.add_analysis(pk, inds, timeline, suggestion)
            st.session_state["current_incident"] = pk
            st.success(f"Incident {clean_id} created with {len(evidence)} evidence item(s). Suggestions are preliminary; review each source.")
            st.rerun()
        except (ValueError, IntakeError) as exc: st.error(str(exc))

elif page in ["Timeline Analysis", "Indicators & Assets", "Classification", "Report Generator", "Review & Approval"]:
    data = current_data()
    if not data:
        st.title(page); st.info("Select or create an incident first.")
    elif page == "Timeline Analysis":
        st.title("Timeline Analysis")
        if data["timeline"]:
            df = pd.DataFrame(data["timeline"])
            df = df.rename(columns={"evidence_id":"Evidence ID","original_timestamp":"Original timestamp","normalized_timestamp":"Normalized UTC","flag":"Review flag","text":"Observed source text"})
            st.dataframe(df[["evidence_id","Original timestamp","Normalized UTC","Review flag","Observed source text"]], use_container_width=True, hide_index=True)
            st.caption("Only timezone-aware timestamps are normalized. Missing or naive timestamps are not guessed.")
        else: st.info("No timeline analysis found. Reprocess evidence by generating a report from the intake workflow.")
    elif page == "Indicators & Assets":
        st.title("Observed Indicators & Assets")
        if data["indicators"]:
            rows=[]
            for x in data["indicators"]: rows.append({"Type":x["type"],"Observed value":x["value"],"Evidence IDs":", ".join(json.loads(x["evidence_ids"])),"Status":"Observed in evidence"})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else: st.info("No indicators were extracted.")
        st.caption("Passive local extraction only: no DNS, reputation, scanning, or suspicious-infrastructure connections.")
    elif page == "Classification":
        st.title("Suggested Classification")
        suggestion = classify(evidence_for(data))
        st.warning("Rule-based suggestion only — not a confirmed incident finding or impact assessment.")
        a,b,c = st.columns(3); a.metric("Category", suggestion["category"]); b.metric("Suggested severity", suggestion["severity"]); c.metric("Confidence", suggestion["confidence"])
        st.write(suggestion["rationale"])
        st.write("Supporting evidence: " + (", ".join(suggestion["evidence_ids"]) or "None found"))
        with st.expander("Configurable rubric"):
            st.write("Category is selected by matching configured keyword phrases in evidence. Severity: High for explicit high-impact terms (e.g., ransomware, exfiltration, critical system, DDoS); Medium for malware/phishing/unauthorized-login terms; otherwise Low. This deliberately simple rubric needs analyst validation.")
    elif page == "Report Generator":
        st.title("Report Generator")
        if st.button("Generate new evidence-linked draft", type="primary"):
            evidence=evidence_for(data); indicators=extract_indicators(evidence); timeline=build_timeline(evidence); suggestion=classify(evidence)
            report=generate_report(data["incident"], evidence, timeline, indicators, suggestion)
            report_id=db.save_report(current_pk, report, "Draft")
            st.success(f"Draft created: {report_id}"); st.rerun()
        reportrec=current_report(data)
        if reportrec:
            st.caption(f"Latest report status: **{reportrec['status']}** · generated {reportrec['created_at']}")
            report=reportrec["report"]
            with st.expander("Evidence-linked preview", expanded=True):
                st.write(report["executive_summary"]["text"]); st.write(f"Suggested: {report['classification']['category']} / {report['classification']['severity']}")
                st.json({"timeline":report["timeline"],"observed_indicators":report["observed_indicators"],"unknowns":report["unknowns_and_evidence_gaps"]}, expanded=False)
            st.info("Edit and approve in **Review & Approval**. Generated reports are never approved automatically.")
        else: st.info("Generate a report draft from the analyzed evidence.")
    elif page == "Review & Approval":
        st.title("Review & Approval")
        reportrec=current_report(data)
        if not reportrec: st.info("Generate a report draft first.")
        else:
            report=reportrec["report"]
            st.warning(f"Current status: {reportrec['status']}. Approval is a human action and is recorded locally.")
            with st.form("review_form"):
                reviewer=st.text_input("Reviewer identity", value="")
                report["executive_summary"]["text"]=st.text_area("Executive summary", report["executive_summary"]["text"], height=100)
                report["classification"]["category"]=st.selectbox("Category", [report["classification"]["category"],"Phishing","Malware","Suspicious login","Denial of service","Unclassified"])
                report["classification"]["severity"]=st.selectbox("Severity", [report["classification"]["severity"],"Low","Medium","High","Critical"])
                report["potential_impact"]["text"]=st.text_area("Potential impact (hypothesis; label evidence)", report["potential_impact"]["text"])
                report["confirmed_impact"]["text"]=st.text_area("Confirmed impact", report["confirmed_impact"]["text"])
                report["response_actions_completed"]["text"]=st.text_area("Response actions completed", report["response_actions_completed"]["text"])
                report["lessons_learned"]=st.text_area("Lessons learned", report["lessons_learned"])
                report["unknowns_and_evidence_gaps"]=st.text_area("Unknowns / evidence gaps (one per line)", "\n".join(report["unknowns_and_evidence_gaps"])).splitlines()
                review_note=st.text_input("Review note (optional)")
                c1,c2,c3=st.columns(3); save=c1.form_submit_button("Save edits · In Review"); approve=c2.form_submit_button("Approve report"); reject=c3.form_submit_button("Reject report")
            if save or approve or reject:
                try:
                    reviewer=validate_reviewer(reviewer)
                    status="In Review" if save else ("Approved" if approve else "Rejected")
                    report["review"]["status"]=status; report["review"]["reviewer"]=reviewer
                    report["review"]["approved_at"]=db.now_utc() if approve else None
                    db.update_report(reportrec["id"],report,status); db.record_review(reportrec["id"],reviewer,status,review_note)
                    with db.connect() as conn: conn.execute("UPDATE incidents SET status=? WHERE id=?",(status,current_pk))
                    st.success(f"Report status recorded as {status}."); st.rerun()
                except ValueError as exc: st.error(str(exc))

elif page == "Export & Audit":
    st.title("Export & Audit History")
    data=current_data()
    if data:
        reportrec=current_report(data)
        if reportrec:
            st.caption(f"Latest report: {reportrec['status']} — exports will carry this status label.")
            report=reportrec["report"]; status=reportrec["status"]
            st.download_button("Download report JSON", report_json(report,status), file_name=f"{report['incident_id']}.json", mime="application/json")
            st.download_button("Download report TXT", report_text(report,status), file_name=f"{report['incident_id']}.txt", mime="text/plain")
            try: st.download_button("Download report PDF", report_pdf(report,status), file_name=f"{report['incident_id']}.pdf", mime="application/pdf")
            except RuntimeError as exc: st.warning(str(exc))
        else: st.info("Generate a report before exporting.")
    else: st.info("Select an incident to view its exports.")
    st.subheader("Recent audit events")
    audit=db.list_audit()
    if audit: st.dataframe(pd.DataFrame(audit), use_container_width=True, hide_index=True)
    else: st.caption("No audit events recorded.")
    if data:
        with st.expander("Retention / deletion"):
            st.warning("Deleting an incident permanently removes associated evidence, reports, reviews, and audit rows due to database cascade rules.")
            confirm=st.checkbox(f"Confirm permanent deletion of {data['incident']['incident_id']}")
            if st.button("Delete selected incident", disabled=not confirm): db.delete_incident(current_pk); st.success("Incident deleted."); st.rerun()

st.sidebar.caption("Prototype · local SQLite · no external AI transmission")
