> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Branching Combinators

- [x] 1.1 Implement `Or`, `And`, `Not` classes in `src/tiportfolio/algo.py`
- [x] 1.2 Export `Or`, `And`, `Not` in `src/tiportfolio/__init__.py` and add to `__all__`
- [x] 1.3 Create `tests/test_combinators.py` with tests: truth tables for Or/And/Not, short-circuit verification, nested composition (`Or(And(...), Not(...))`)
- [x] 1.4 Run tests — all pass

## 2. Signal Expansion

- [x] 2.1 Implement `Signal.Schedule(day=int)` logic in `src/tiportfolio/algos/signal.py` — NYSE calendar resolution with `next_trading_day` flag
- [x] 2.2 Implement `Signal.Quarterly` in `src/tiportfolio/algos/signal.py` — delegates to `Or(*[Schedule(month=m, day=day) for m in months])`
- [x] 2.3 Add tests to `tests/test_signal.py`: Schedule day=int (trading day hit, non-trading day snap-forward, next_trading_day=False, day=31 in Feb), Quarterly (default 4 fires/year, custom months)
- [x] 2.4 Run tests — all pass

## 3. Selection Expansion

- [x] 3.1 Implement `Select.Momentum` in `src/tiportfolio/algos/select.py` — lookback return ranking with lag
- [x] 3.2 Implement `Select.Filter` in `src/tiportfolio/algos/select.py` — boolean gate with external data condition
- [x] 3.3 Add tests to `tests/test_select.py`: Momentum (top-2 of 3 with known returns, sort_descending=False, lag offset), Filter (pass continues queue, fail halts queue, selected unchanged)
- [x] 3.4 Run tests — all pass

## 4. Weighting Expansion

- [x] 4.1 Implement `Weigh.Ratio` in `src/tiportfolio/algos/weigh.py` — normalised explicit weights
- [x] 4.2 Implement `Weigh.BasedOnHV` in `src/tiportfolio/algos/weigh.py` — volatility-targeted scaling using diagonal covariance
- [x] 4.3 Add tests to `tests/test_weigh.py`: Ratio (normalisation, missing ticker gets 0, already-summing-to-1), BasedOnHV (scale down, scale up/leverage, zero-vol edge case, uses bars_per_year)
- [x] 4.4 Run tests — all pass

## 5. Integration Verification

- [x] 5.1 Update `tests/test_e2e.py` — add import checks for `ti.Or`, `ti.And`, `ti.Not`
- [x] 5.2 Run full test suite (`uv run python -m pytest`) — all existing + new tests pass
- [x] 5.3 Verify Chunk 2 deliverable example runs: quarterly rebalance with Ratio weights, momentum with branching (And + Not)
