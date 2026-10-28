# Faculty Demonstration Script (3–5 minutes)

**Opening (20 seconds):** “This is a local incident-report drafting assistant. It helps organize authorized, sanitized evidence. It does not declare an incident confirmed, and it does not connect to suspicious systems or send evidence to an external AI service.”

**1. Intake (45 seconds):** Open Evidence Intake. Enter `IR-DEMO-001`, a reporting period, and upload `sample_data/sample_phishing.txt`. Explain the 5 MB limit and supported formats. Submit and point out that the app assigns E-001, E-002, etc.

**2. Timeline (40 seconds):** Open Timeline Analysis. Show source timestamp and normalized UTC columns. Explain that timezone-aware events are normalized, while missing or timezone-naive timestamps remain flagged rather than guessed.

**3. Indicators and classification (45 seconds):** Show the observed IP and host with evidence IDs. Open Classification and explain that category/severity are keyword-rule suggestions with confidence and rationale, not conclusions.

**4. Report draft (45 seconds):** Generate a report. Highlight the timeline, evidence claim references, and explicit “Not supported by available evidence” statements for confirmed impact or response actions lacking support.

**5. Human review and export (60 seconds):** Enter a reviewer name, modify a section, save In Review, then explicitly approve (or reject) the report. Explain the database review/audit record. Export a PDF or JSON and show the status label.

**Closing (20 seconds):** “The strongest design choices are evidence traceability, uncertainty visibility, local-only processing, and human approval. Limitations include simple heuristics and the absence of production authentication or immutable forensic storage.”

## Suggested discussion questions
- Why is an IP address extracted from evidence not automatically labelled malicious?
- Why are timezone-naive timestamps not normalized to UTC?
- What controls would be required before introducing an external LLM?
- How could evidence hashes and access control improve the design?
