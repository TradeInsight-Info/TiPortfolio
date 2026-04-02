> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Implement Signal.Indicator

- [x] 1.1 Add `Signal.Indicator` class to `src/tiportfolio/algos/signal.py` with `__init__(self, ticker: str, condition: Callable[[pd.Series], bool], lookback: pd.DateOffset, cross: str = "up")`. Validate `cross` in `{"up", "down", "both"}`, raise `ValueError` otherwise.
- [x] 1.2 Implement `__call__`: slice `context.prices[ticker].loc[start:end, "close"]`, call `condition(series)` to get `current_state: bool`. If `self._prev_state is None` (first bar), set it and return False.
- [x] 1.3 Implement edge detection: compare `current_state` vs `self._prev_state`. Fire True if transition matches `self._cross` direction. Update `self._prev_state`.
- [x] 1.4 Handle missing ticker: if `ticker not in context.prices`, return False.

## 2. Write tests

- [x] 2.1 Create `tests/test_signal_indicator.py` with a helper that builds synthetic prices with a known SMA crossover point (e.g., rising prices that cause SMA50 to cross above SMA200 at a specific bar).
- [x] 2.2 Test `cross="up"`: fires exactly once on the bar where condition transitions False→True, not on subsequent True→True bars.
- [x] 2.3 Test `cross="down"`: fires on True→False transition only.
- [x] 2.4 Test `cross="both"`: fires on both directions.
- [x] 2.5 Test first-bar initialisation: never fires on the first call.
- [x] 2.6 Test invalid `cross` value raises `ValueError`.
- [x] 2.7 Test missing ticker returns False without error.
- [x] 2.8 Test composability: `Or(Signal.Monthly(), Signal.Indicator(...))` fires on either event.
- [x] 2.9 Run full test suite: `uv run python -m pytest` — all tests pass.

## 3. Add SMA crossover example

- [x] 3.1 Create `examples/19_sma_crossover.py` — a complete example that uses `Signal.Indicator` with a 50/200 SMA crossover condition on a single ticker (e.g., QQQ). Load CSV data, define the SMA cross condition as a lambda, build a portfolio with `Signal.Indicator(ticker="QQQ", condition=sma_cross, lookback=pd.DateOffset(days=250), cross="up")`, run the backtest, and print `summary()`. Include comments explaining the crossover logic and how edge detection works.
