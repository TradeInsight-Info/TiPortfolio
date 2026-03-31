## Review

### Consistency Check
- Proposal lists one capability (`csv-offline-data`) — spec covers it with 3 requirements.
- Brainstorm chunks A/B/C map to the 3 spec requirements. Consistent.

### Completeness Check
- Partial CSV validation: covers both single and multiple missing tickers. Edge case of empty dict not explicitly tested but would hit same path.
- Examples: spec requires all examples use CSV tickers only. Need to verify which examples need ticker changes.
- E2E: spec requires removal of `patch()` calls — clear and testable.

### Issues Found
None — proposal, brainstorm, and specs are aligned.
