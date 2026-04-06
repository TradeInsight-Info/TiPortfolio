## Review

### Consistency Check
- Proposal lists one new capability `cli-aip` — specs contain one spec file `specs/cli-aip/spec.md`. Consistent.
- Proposal says "all subcommands" — spec covers monthly, quarterly, and the omitted case. Consistent.
- Proposal says "no breaking changes" — correct, `--aip` is additive with default `None`.

### Completeness Check
- 3 requirements with 5 scenarios, all WHEN/THEN format, all testable.
- Edge case covered: AIP omitted (backward compatibility).
- Edge case covered: AIP + leverage combination.

### Issues Found
None. Ready for design.
