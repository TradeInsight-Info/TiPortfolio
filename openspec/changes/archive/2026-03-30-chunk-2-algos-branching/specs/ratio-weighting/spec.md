## ADDED Requirements

### Requirement: Weigh.Ratio assigns explicit weights normalised to full investment
`Weigh.Ratio` SHALL accept `weights: dict[str, float]` and write normalised weights to `context.weights`. Normalisation SHALL divide each weight by `sum(|w|)` so the portfolio is always fully invested.

#### Scenario: Three-asset explicit weights
- **WHEN** `Weigh.Ratio(weights={"QQQ": 0.6, "BIL": 0.3, "GLD": 0.1})` is called with all three tickers in `context.selected`
- **THEN** `context.weights` equals `{"QQQ": 0.6, "BIL": 0.3, "GLD": 0.1}` (already sums to 1.0)

#### Scenario: Weights that don't sum to 1.0
- **WHEN** `Weigh.Ratio(weights={"A": 3.0, "B": 1.0})` is called with both tickers selected
- **THEN** `context.weights` equals `{"A": 0.75, "B": 0.25}` (normalised by sum of absolute values = 4.0)

#### Scenario: Selected ticker missing from weights dict
- **WHEN** `Weigh.Ratio(weights={"QQQ": 0.7, "GLD": 0.3})` is called with `["QQQ", "BIL", "GLD"]` selected
- **THEN** `context.weights` contains only `{"QQQ": 0.7, "GLD": 0.3}` (BIL excluded — position closed on rebalance)

### Requirement: Weigh.Ratio returns True
`Weigh.Ratio.__call__` SHALL always return `True`.

#### Scenario: Always continues queue
- **WHEN** `Weigh.Ratio` is called
- **THEN** it returns `True`
