## ADDED Requirements

### Requirement: Select.Filter gates the algo queue using external data
`Select.Filter` SHALL accept `data: dict[str, pd.DataFrame]` and a `condition: Callable[[dict[str, pd.Series]], bool]`. It SHALL return the boolean result of `condition(row)` where `row` is the current date's data extracted from each DataFrame.

#### Scenario: Condition passes
- **WHEN** `Select.Filter(data=vix_data, condition=lambda row: row["^VIX"]["close"] < 30)` is called and VIX close is 25
- **THEN** it returns `True` and the algo queue continues

#### Scenario: Condition fails
- **WHEN** the same Filter is called and VIX close is 35
- **THEN** it returns `False` and the algo queue halts (no rebalance, positions hold)

### Requirement: Select.Filter does not modify context.selected
`Select.Filter` SHALL NOT modify `context.selected`. It is a boolean gate only.

#### Scenario: Selected unchanged on pass
- **WHEN** Filter returns `True`
- **THEN** `context.selected` remains exactly as set by a prior Select algo

#### Scenario: Selected unchanged on fail
- **WHEN** Filter returns `False`
- **THEN** `context.selected` remains unchanged (though the queue halts, so downstream algos don't run)
