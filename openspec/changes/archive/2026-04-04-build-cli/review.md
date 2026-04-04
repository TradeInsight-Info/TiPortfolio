## Review

### Consistency Check
- All 6 capabilities from the proposal are covered by corresponding spec files
- Signal subcommands cover all 6 Signal algos (Monthly, Quarterly, Weekly, Yearly, EveryNPeriods, Once)
- Select options cover All and Momentum (Filter excluded — requires Python callable)
- Weigh options cover Equally, Ratio, ERC, BasedOnHV (BasedOnBeta excluded — requires base_data)
- Data/Config/Output specs align with the brainstorm's flag inventory

### Completeness Check
- All scenarios are testable via click's CliRunner
- Error cases covered: missing tickers, missing date range, ratio count mismatch, missing --top-n for momentum, missing --target-hv for hv weighting, missing --n/--period for every
- Default behaviors specified for: select (all), ratio (equal), source (yfinance), leverage (1.0), output (summary)

### Issues Found
None — proposal capabilities map 1:1 to spec files. All CLI flags have clear mappings to existing algo constructors. The excluded algos (Signal.VIX, Signal.Indicator, Select.Filter, Weigh.BasedOnBeta) are correctly omitted as they require Python callables or complex data arguments not expressible on the command line.
