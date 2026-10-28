# College Project Brief

## Title
**AI-Powered Cybersecurity Incident Report Assistant**

## Abstract
Cybersecurity investigations often combine alerts, notes, and logs from multiple sources. Manually organizing these records into a consistent timeline and report can be time-consuming and can lead to unsupported conclusions. This project implements a local, evidence-first assistant that accepts sanitized incident material, assigns evidence identifiers, extracts explicit timestamps and indicators, suggests a category and severity using transparent rules, and produces a structured report draft whose observed claims point back to evidence. SQLite stores incident and review records, while a Streamlit interface supports investigation and human review. The application uses a deterministic local fallback rather than sending evidence to an external model. Reports remain drafts until a named analyst explicitly approves them. The prototype demonstrates explainability, uncertainty handling, safe data intake, and analyst oversight; it is educational and is not a replacement for a production incident-response platform.

## Problem statement
Analysts must consolidate heterogeneous evidence into a clear incident narrative. A rushed process can obscure chronology, lose source references, or mix facts with hypotheses. The project addresses this documentation problem by organizing evidence and supporting—not replacing—human analysis.

## Objectives
1. Validate and parse sanitized TXT, LOG, JSON, and CSV evidence.
2. Preserve source excerpts and assign unique evidence IDs.
3. Normalize timezone-aware timestamps to UTC and flag unknown/ambiguous times.
4. Extract indicators that appear in the evidence, without network interaction.
5. Explain configurable rule-based classification and severity suggestions.
6. Generate a structured evidence-linked report draft with explicit unknowns.
7. Provide human editing, review, approval/rejection, basic audit history, and status-labelled exports.
8. Demonstrate tests, modular design, and local SQLite persistence.

## Methodology
The workflow is: (1) analyst enters an incident record and supplies authorized sanitized evidence; (2) intake validates extension, size, and UTF-8 content; (3) evidence items are stored with unique IDs; (4) local parsing extracts timestamps and indicators, while a transparent keyword rubric proposes category and severity; (5) the report generator creates a structured draft and labels unsupported facts; (6) analyst inspects, edits, and records In Review, Approved, or Rejected; (7) exports preserve the review state. The application is designed to run locally and does not transmit the evidence to an external AI service.

## Modules
- `app.py`: Streamlit dashboard and forms.
- `incident_assistant/ingestion.py`: upload validation and TXT/LOG/JSON/CSV parsing.
- `timeline.py`: timestamp extraction, UTC conversion, and uncertainty flags.
- `indicators.py`: passive regex extraction of IPs, domains, hashes, hostnames, usernames, and event IDs.
- `classification.py`: explainable keyword-based incident and severity suggestion.
- `ai_adapter.py`: local fallback boundary; no external model call is enabled.
- `report_generator.py`: structured report with evidence references and gaps.
- `database.py`: SQLite persistence, records, review actions, and audit events.
- `export_utils.py`: JSON, TXT, PDF exports with draft labels.
- `backend/main.py`: optional localhost FastAPI health and listing routes.
- `tests/`: automated verification using synthetic inputs.

## Advantages
- Runs locally with a clear, demonstrable workflow.
- Keeps report claims tied to source evidence IDs.
- Flags uncertainty instead of inventing timestamps or confirmed impact.
- Uses an explainable rubric and highlights its suggestions as unconfirmed.
- Does not execute uploaded data or perform unauthorized external lookups.
- Requires an explicit human approval action; provides review status and basic audit records.

## Limitations
- Rule-based extraction and classification are deliberately simple and can miss context or produce false matches.
- No production-grade authentication, role-based access, encryption policy, tamper-proof audit log, forensic chain of custody, or multi-tenant isolation.
- Timestamp parsing does not resolve locale ambiguity or infer source timezone.
- The report generator cannot validate analyst-entered edits or automatically source every new claim.
- No external LLM integration is enabled; using an LLM would require a separate privacy and security review.
- Not certified against any security or regulatory standard and not suitable as the sole record of a real incident.

## Future enhancements
- Add authenticated role-based access and encrypted, managed storage.
- Add immutable evidence hashes and chain-of-custody records.
- Implement schema-aware JSON/CSV adapters and configurable event parsers.
- Add analyst-configurable severity rubric and taxonomy.
- Add claim-level evidence checking for analyst-edited report sections.
- Add optional approved LLM adapter with redaction, provider controls, and prompt-injection defenses.
- Add audit-log export, retention policy controls, localization, and deployment hardening.

## Evaluation criteria
The project can be evaluated on input validation, correct handling of known/naive timestamps, indicator evidence links, transparent classification rationale, non-fabrication of unsupported impacts, database relationships, review-state transitions, export labels, automated tests, and clarity of documentation.
