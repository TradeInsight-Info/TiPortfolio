# Purpose

TBD

## Requirements

### Requirement: Compute mean excess return
`compute_metrics()` SHALL compute `mean_excess_return` as the annualised mean of daily excess returns: `excess.mean() * periods_per_year`.

#### Scenario: Mean excess return with positive returns
- **WHEN** equity series has consistently positive daily returns above risk-free rate
- **THEN** `mean_excess_return` is a positive float in the returned metrics dict

#### Scenario: Mean excess return with empty series
- **WHEN** equity series is empty or has fewer than 2 points
- **THEN** `mean_excess_return` is `nan`

### Requirement: Compute Sortino ratio
`compute_metrics()` SHALL compute `sortino_ratio` as annualised mean excess return divided by annualised downside deviation (std of returns below daily risk-free rate, multiplied by `sqrt(periods_per_year)`).

#### Scenario: Sortino ratio with mixed returns
- **WHEN** equity series contains both positive and negative excess return days
- **THEN** `sortino_ratio` is a finite float; higher than Sharpe ratio when downside vol < total vol

#### Scenario: Sortino ratio with no downside
- **WHEN** all daily returns are above the risk-free rate (no down days)
- **THEN** `sortino_ratio` is `nan` (not `inf`)

#### Scenario: Sortino ratio with empty series
- **WHEN** equity series is empty or has fewer than 2 points
- **THEN** `sortino_ratio` is `nan`

### Requirement: Canonical metric ordering
`compute_metrics()` SHALL return metrics in this order: `sharpe_ratio`, `sortino_ratio`, `mar_ratio`, `cagr`, `max_drawdown`, `kelly_leverage`, `mean_excess_return`.

#### Scenario: Dict key order matches canonical order
- **WHEN** `compute_metrics()` is called with a valid equity series
- **THEN** `list(metrics.keys())` equals `["sharpe_ratio", "sortino_ratio", "mar_ratio", "cagr", "max_drawdown", "kelly_leverage", "mean_excess_return"]`
