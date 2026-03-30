## ADDED Requirements

### Requirement: Select.Momentum ranks tickers by lookback return
`Select.Momentum` SHALL select the top `n` tickers from `context.selected` ranked by cumulative return over the lookback period. It SHALL only operate on string tickers (not `Portfolio` children).

#### Scenario: Select top 2 of 3 tickers
- **WHEN** `Select.Momentum(n=2, lookback=pd.DateOffset(months=1))` is called with 3 tickers in `context.selected`
- **THEN** `context.selected` contains the 2 tickers with the highest cumulative return over the past month

#### Scenario: Sort descending (default)
- **WHEN** `Select.Momentum(n=1, lookback=pd.DateOffset(months=1), sort_descending=True)` is called
- **THEN** `context.selected` contains the single ticker with the highest return

#### Scenario: Sort ascending (worst performers)
- **WHEN** `Select.Momentum(n=1, lookback=pd.DateOffset(months=1), sort_descending=False)` is called
- **THEN** `context.selected` contains the single ticker with the lowest return

### Requirement: Select.Momentum applies lag to avoid look-ahead bias
The lookback window end SHALL be offset by `lag` (default `pd.DateOffset(days=1)`) before the current date. The return is computed from `(context.date - lag - lookback)` to `(context.date - lag)`.

#### Scenario: Default 1-day lag
- **WHEN** Momentum is evaluated on date `2024-03-15` with `lookback=DateOffset(months=1)` and default lag
- **THEN** returns are computed from `2024-02-14` to `2024-03-14` (not including the current date)

### Requirement: Select.Momentum returns True
`Select.Momentum.__call__` SHALL always return `True` (queue continues after selection).

#### Scenario: Always continues queue
- **WHEN** `Select.Momentum` is called (regardless of selection result)
- **THEN** it returns `True`
