## Context

The BacktestEngine currently accepts `price_dfs` as a dictionary where each value is a pandas Series containing only closing prices. This design limits flexibility as users cannot easily provide full OHLC (Open, High, Low, Close) data or additional price information like volume. The `prices_dict_from_long_format` function exists but is not useful for this purpose. Additionally, DataFrame indices may lack proper timezone information, leading to potential issues with date alignment and market calendar operations.

The project uses pandas for data manipulation and relies on timezone-aware datetime indices for accurate rebalancing calculations based on NYSE trading days.

## Goals / Non-Goals

**Goals:**
- Refactor BacktestEngine to accept `price_dfs` as a dictionary of DataFrames with OHLC columns
- Implement an index normalization utility to ensure DataFrame indices have proper NYSE timezone information
- Remove dependency on `prices_dict_from_long_format` function
- Add automated tests to validate consistency between CSV price files and DataFrame equivalents

**Non-Goals:**
- Change rebalance scheduling or calculation logic
- Modify existing engine parameters other than `price_dfs`
- Add support for non-OHLC data formats

## Decisions

- **Data Structure**: Use pandas DataFrame with standard OHLC columns ('open', 'high', 'low', 'close') plus optional 'volume'. Index must be timezone-aware datetime. Rationale: Standard financial data format, allows full price information access. Alternative: Keep Series but add OHLC columns - rejected because Series doesn't handle multiple price types well.
- **Index Normalization**: Create `normalize_price_index(df)` utility that converts index to datetime if needed, adds 'America/New_York' timezone if missing, and sets time to 00:00:00. Rationale: Ensures consistent timezone handling for market calendar operations. Alternative: Require users to provide properly formatted data - rejected because it increases friction and potential for errors.
- **Test Structure**: Use parametrized pytest fixtures to test each symbol (BIL, QQQ, GLD) by comparing CSV 'price' column values with DataFrame 'close' column values. Rationale: Automated validation prevents data inconsistencies. Alternative: Manual checks - rejected because it's error-prone and not maintainable.
- **Breaking Change**: Accept this as necessary for improved functionality. Rationale: The change enables more powerful price data handling. Alternative: Provide backward compatibility - rejected because it would complicate the codebase unnecessarily.

## Risks / Trade-offs

- **[Breaking Change] Existing code passing Series dict will fail → Mitigation: Update all callers in codebase and document migration in release notes.
- **[Performance] DataFrames use more memory than Series → Mitigation: Accept trade-off as DataFrames provide more functionality and memory is not a critical constraint.
- **[Data Validation] Index normalization assumes NYSE timezone → Mitigation: Document assumption and provide clear error messages if timezone cannot be determined.

## Migration Plan

1. Update BacktestEngine.__init__ to apply index normalization to each DataFrame in price_dfs
2. Modify engine methods that access price data to use df['close'] instead of series values
3. Update all test and example code to pass DataFrame dict instead of Series dict
4. Add new data validation tests to test suite
5. Remove prices_dict_from_long_format usage from codebase

**Rollback Strategy**: Revert BacktestEngine changes and restore Series dict handling if critical issues arise.

## Open Questions

- How should volume data be handled when not present in DataFrames? (Volume is optional column)
- Should index normalization be applied at DataFrame creation time or in the engine? (Decision: in engine for consistency)
