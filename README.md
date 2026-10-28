# AI-Powered Cybersecurity Incident Report Assistant

A locally runnable, evidence-first incident-reporting prototype for authorized educational and defensive use. It ingests sanitized TXT, LOG, JSON, and CSV evidence, builds an explainable UTC timeline where timestamps contain an explicit timezone, extracts indicators found in the submitted evidence, suggests incident category/severity using transparent keyword rules, and generates a draft report with evidence IDs. An analyst edits and explicitly approves or rejects the report before it is labelled approved.

> **Safety and scope:** Use synthetic or explicitly authorized, sanitized data only. This is not a production incident-response platform. It does not scan networks, query threat intelligence, connect to suspicious infrastructure, execute uploaded content, or transmit incident data to an external AI provider. Classification is a basic heuristic suggestion, not a finding. Access control is limited to the local application process; do not expose it to an untrusted network.

## Features

- Streamlit dashboard, evidence intake, timeline, observed indicators, classification, report generation, human review, and exports.
- Optional localhost-only FastAPI health/listing API.
- SQLite persistence for incidents, evidence, indicators, timeline events, reports, reviews, and audit entries.
- UTF-8 text uploads limited to 5 MB per file; supported extensions: `.txt`, `.log`, `.json`, `.csv`.
- Evidence IDs and claim-to-evidence references. Unsupported impact/actions are explicitly marked.
- Timestamps with offsets are normalized to UTC. Naive/missing timestamps are flagged, never assigned a guessed timezone.
- Draft status on unapproved JSON/TXT/PDF exports; deletion control for stored incidents.
- Synthetic sample evidence and pytest test suite.

## Requirements

Python 3.10+ (tested with Python 3.12), pip, and a modern browser. SQLite is included with Python.

## Install and run

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints a local URL, normally `http://localhost:8501`. The SQLite file `incident_reports.db` is created on first launch. To use another location, copy `.env.example` to `.env` and set `INCIDENT_DB_PATH`; note that this simple example does not automatically load `.env`, so export the variable in your shell before starting Streamlit:

```bash
export INCIDENT_DB_PATH="$PWD/incident_reports.db"
```

On PowerShell: `$env:INCIDENT_DB_PATH = "$PWD\\incident_reports.db"`.

### Optional FastAPI service

In a separate terminal with the virtual environment active:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/incidents`. Bind to localhost only. The API intentionally exposes no evidence or report-write endpoints in this starter implementation.

## Demonstration steps

1. Open **Evidence Intake**. Enter incident ID `IR-DEMO-001`, select reporting period `2026-10-28`, and upload `sample_data/sample_phishing.txt`.
2. Create and analyze. Notice the app states that the data remains local.
3. Inspect **Timeline Analysis**. The timezone-aware timestamps sort in UTC; missing/naive times would remain flagged.
4. Inspect **Indicators & Assets** and **Classification**. Check each observed value's evidence ID and the keyword-rule rationale.
5. In **Report Generator**, create a draft. Unsupported confirmed impact and response details remain explicitly unsupported.
6. In **Review & Approval**, enter reviewer identity, edit report sections, and choose **Save edits · In Review**, **Approve report**, or **Reject report**. Approval is never automatic.
7. In **Export & Audit**, download TXT, JSON, or PDF. A report not approved is labelled as a draft. Review local audit history.

## Tests

```bash
pytest -q
```

The tests cover supported and invalid uploads, malformed input, timestamps, indicator extraction, classification, evidence linking, unsupported-impact handling, fallback mode, exports, and database operations. Tests use a temporary SQLite database.

## Project layout

```text
app.py                         Streamlit interface
backend/main.py                Optional FastAPI routes
incident_assistant/            Intake, analysis, database, reporting, exports
sample_data/                   Synthetic example evidence
reports/                       Demonstration output
 tests/                         Automated tests
 docs/                          Architecture and college-project materials
requirements.txt
.env.example
```

## Data handling and limitations

- Files are parsed as data only; the software never executes their contents. They may still contain sensitive material, so sanitize before upload.
- The default `AIAdapter` always uses deterministic local rules. Presence of an API key does not cause any network request. A real provider adapter would require explicit privacy, retention, prompt-injection, and authorization review before implementation.
- CSV/JSON are rendered as text values. This prototype does not preserve a full forensic chain of custody, cryptographic signatures, immutable storage, RBAC, SSO, encryption-at-rest configuration, or multi-user concurrency guarantees.
- The audit table records basic actions, but this is not tamper-proof auditing. Deleting an incident also deletes its related records.
- Classification terms and severity rubric are intentionally small and configurable in `incident_assistant/classification.py`; false positives and false negatives are expected.
- Timestamp parsing is conservative. Ambiguous locale-specific timestamps may not be normalized; review original values and source timezone.
- The report generator only summarizes source records at a coarse level. Every claim still needs analyst verification. Editing a report does not automatically add evidence references to newly written claims.
- No formal security certification or compliance claim is made.

## Troubleshooting

- `ModuleNotFoundError`: activate `.venv` and run `pip install -r requirements.txt` from the project root.
- Port 8501 is busy: run `streamlit run app.py --server.port 8502`.
- PDF download unavailable: ensure `reportlab` installed from requirements.
- Invalid upload: verify UTF-8 text encoding and one of TXT/LOG/JSON/CSV; maximum is 5 MB per file.
- No timeline UTC values: source timestamps may omit a timezone. The app flags rather than guesses.
- Local database reset: stop the app, back up `incident_reports.db` if needed, then remove it to create a clean database on next launch.

## Git and GitHub

Initialize/version the project locally:

```bash
git init
git add .
git commit -m "Build incident report assistant"
```

Review files and remove any real incident content or local database before pushing to GitHub. `.gitignore` excludes databases, environments, and `.env` files. Do not commit secrets or real sensitive evidence.
