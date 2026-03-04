## 1. Implement New Rebalance Schedules in Calendar

- [x] 1.1 Add "weekly_monday", "weekly_wednesday", "weekly_friday", "never" to VALID_SCHEDULES in calendar.py
- [x] 1.2 Add weekly schedule handling in get_rebalance_dates function using pandas 'W-MON' etc. frequencies
- [x] 1.3 Add "never" schedule handling to return empty DatetimeIndex
- [x] 1.4 Use Tuesday if Monday market is closed (same for Wednesday and Friday), create a util get_next_market_day(date) @market_calendar.py based on pandas_market_calendars

## 2. Refactor BacktestEngine to Abstract Base Class

- [x] 2.1 Import ABC from abc module in engine.py
- [x] 2.2 Make BacktestEngine inherit from ABC
- [x] 2.3 Add @abstractmethod decorator to the run method

## 3. Add Freezing Time Support to Volatility Engine

- [x] 3.1 Add freezing_days parameter (default 0) to VolatilityBasedEngine.__init__
- [x] 3.2 Implement freezing logic in VolatilityBasedEngine.run to skip rebalances within freezing period

## 5. Refactor compare_strategies

- [x] 5.1 Modify compare_strategies in report.py to accept *results instead of two named results, and include kelly_leverage and total_fee in the comparison metrics

## 6. Update start_of_month_rebalance.ipynb

- [x] 6.1 Add new cell comparing all three results (result, result_qqq_only, result_never) using the refactored compare_strategies

## 7. Update vix_target_rebalance.ipynb

- [x] 7.1 Add new strategy to use freezing_days=30 in VolatilityBasedEngine and compare the results with the original VIX strategy

## 8. Run Tests

- [x] 8.1 Run pytest on all tests to ensure they pass

## 9. Update plot_strategy_comparison_interactive

- [x] 9.1 Modify plot_strategy_comparison_interactive in report.py to accept *strategies and names=None parameters
- [x] 9.2 Update the call in vix_target_rebalance.ipynb to use names=["VIX regime (QQQ/BIL/GLD)", "Long QQQ"]

## 10. Update Tests for Changes

- [x] 10.1 Review and update any failing tests due to the changes in plot_strategy_comparison_interactive and other modifications
