# Development Notes

- Keep all examples synthetic and use documentation-reserved IP ranges such as 192.0.2.0/24, 198.51.100.0/24, and 203.0.113.0/24.
- Parsers must treat bytes as inert input. Do not add shell execution, macros, or dynamic evaluation of uploaded fields.
- Any new report statement should carry evidence IDs or be explicitly identified as a recommendation, hypothesis, or unknown.
- Do not infer maliciousness from indicator format alone. Passive extraction is not reputation analysis.
- Do not enable external AI transmission without an explicit data-flow review and user-facing opt-in.
- Keep SQLite queries parameterized, and maintain tests for malformed input and status labels.
