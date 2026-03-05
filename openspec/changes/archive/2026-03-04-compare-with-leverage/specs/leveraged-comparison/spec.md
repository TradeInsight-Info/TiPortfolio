## ADDED Requirements

### Requirement: compare_strategies accepts leverage and loan rate parameters
`compare_strategies()` SHALL accept two new optional keyword parameters: `leverages` (float or list of float, default `1.0`) and `yearly_loan_rates` (float or list of float, default `0.0`). When passed as lists, each must have the same length as `results`.

#### Scenario: Scalar leverage applied to all strategies
- **WHEN** `compare_strategies(r1, r2, leverages=1.5)` is called
- **THEN** the same leverage of 1.5 is applied to every strategy's metrics

#### Scenario: Per-strategy leverage list
- **WHEN** `compare_strategies(r1, r2, leverages=[1.0, 1.5])` is called
- **THEN** r1 is compared at 1.0× and r2 at 1.5×

#### Scenario: Mismatched list length raises ValueError
- **WHEN** `leverages` or `yearly_loan_rates` is a list with length ≠ `len(results)`
- **THEN** `ValueError` is raised with a message indicating the mismatch

### Requirement: Leverage adjusts max_drawdown
When leverage L is applied to a strategy, the displayed `max_drawdown` in the comparison table SHALL be `L × original_max_drawdown`.

#### Scenario: Drawdown scales with leverage
- **WHEN** a strategy has `max_drawdown = 0.20` and leverage `L = 1.5`
- **THEN** the comparison row shows `max_drawdown = 0.30`

#### Scenario: No leverage leaves drawdown unchanged
- **WHEN** leverage is `1.0` (default)
- **THEN** `max_drawdown` in the comparison equals the original metric value

### Requirement: Leverage and loan rate adjust CAGR
The displayed `cagr` in the comparison table SHALL be `L × original_cagr − (L − 1) × yearly_loan_rate`.

#### Scenario: Positive CAGR with leverage and loan cost
- **WHEN** a strategy has `cagr = 0.10`, `L = 1.5`, `yearly_loan_rate = 0.05`
- **THEN** displayed `cagr = 1.5 × 0.10 − 0.5 × 0.05 = 0.125`

#### Scenario: No leverage and zero loan rate leaves CAGR unchanged
- **WHEN** leverage is `1.0` and `yearly_loan_rate` is `0.0`
- **THEN** `cagr` in the comparison equals the original metric value

### Requirement: MAR ratio recomputed from leveraged metrics
The displayed `mar_ratio` in the comparison table SHALL be `leveraged_cagr / leveraged_max_drawdown`. If `leveraged_max_drawdown` is 0, `mar_ratio` SHALL be `nan`.

#### Scenario: MAR recomputed after leverage
- **WHEN** leveraged_cagr = 0.125 and leveraged_max_drawdown = 0.30
- **THEN** displayed `mar_ratio = 0.125 / 0.30 ≈ 0.4167`

#### Scenario: Zero drawdown yields nan MAR
- **WHEN** original `max_drawdown = 0.0` (so leveraged drawdown also 0)
- **THEN** `mar_ratio` in the comparison is `nan`

### Requirement: Sharpe and Sortino ratios are unchanged by leverage
The displayed `sharpe_ratio` and `sortino_ratio` in the comparison table SHALL equal the original values regardless of leverage or loan rate.

#### Scenario: Sharpe unchanged at any leverage
- **WHEN** a strategy has `sharpe_ratio = 1.5` and leverage `L = 2.0`
- **THEN** the comparison row shows `sharpe_ratio = 1.5`

### Requirement: Column headers decorated when leverage is applied
When any strategy has leverage ≠ 1.0, the corresponding column name in the output DataFrame SHALL be decorated with `(L{L}x)`. When both leverage ≠ 1.0 and `yearly_loan_rate` ≠ 0.0, the decoration SHALL include both: `(L{L}x, r{rate:.1%})`.

#### Scenario: Column name decorated for leveraged strategy
- **WHEN** `names=["A", "B"]` and `leverages=[1.0, 1.5]`
- **THEN** the DataFrame columns are `["A", "B (L1.5x)", "better"]`

#### Scenario: No decoration when all leverages are 1.0
- **WHEN** all strategies use default leverage `1.0`
- **THEN** column names remain exactly as provided in `names`

### Requirement: plot_strategy_comparison_interactive accepts leverage and loan rate parameters
`plot_strategy_comparison_interactive()` SHALL accept `leverages` (float or list of float, default `1.0`) and `yearly_loan_rates` (float or list of float, default `0.0`). When passed as lists, each must have the same length as `strategies`. Invalid lengths SHALL raise `ValueError`.

#### Scenario: Scalar leverage accepted by chart function
- **WHEN** `plot_strategy_comparison_interactive(s1, s2, leverages=1.5)` is called
- **THEN** the figure is returned without error and both traces use leveraged equity curves

#### Scenario: Mismatched list length raises ValueError in chart function
- **WHEN** `leverages` is a list with length ≠ number of strategies
- **THEN** `ValueError` is raised

### Requirement: Chart plots leveraged equity curves
When leverage L ≠ 1.0 or `yearly_loan_rate` ≠ 0.0 for a strategy, `plot_strategy_comparison_interactive()` SHALL plot a reconstructed leveraged equity curve instead of the raw curve. The curve SHALL be computed as: `equity_lev[0] = equity_curve.iloc[0]`, `equity_lev[t] = equity_lev[0] × cumprod(1 + L × r_t − (L−1) × rate/252)`.

#### Scenario: Starting equity preserved after leverage reconstruction
- **WHEN** a strategy's equity curve starts at value V and leverage L = 1.5 is applied
- **THEN** the first plotted Y-value for that trace is V (unchanged starting equity)

#### Scenario: Leveraged curve diverges from raw curve
- **WHEN** leverage L = 1.5 is applied to a strategy with non-zero daily returns
- **THEN** the plotted trace Y-values (after index 0) differ from the raw equity curve values

#### Scenario: Default params produce identical chart to unleveraged
- **WHEN** `plot_strategy_comparison_interactive()` is called with default leverage and loan rate
- **THEN** the trace Y-values match the original equity curves exactly
