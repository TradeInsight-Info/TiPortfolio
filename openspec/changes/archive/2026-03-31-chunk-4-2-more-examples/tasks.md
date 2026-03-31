> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Chunk 2 Examples

- [x] 1.1 Create `examples/10_quarterly_ratio.py` — Signal.Quarterly + Weigh.Ratio with QQQ/BIL/GLD
- [x] 1.2 Create `examples/11_momentum_top_n.py` — Select.Momentum top-3 of a 6-ticker universe, monthly rebalance
- [x] 1.3 Create `examples/12_branching_skip_december.py` — And/Not combinators: monthly rebalance but skip December
- [x] 1.4 Create `examples/13_volatility_targeting.py` — Weigh.BasedOnHV targeting 15% annualised volatility
- [x] 1.5 Create `examples/16_weekly_rebalance.py` — Signal.Weekly end-of-week rebalance

## 2. Chunk 3 Examples

- [x] 2.1 Create `examples/14_dollar_neutral.py` — Parent/child tree: long leg (top-3 momentum) + short leg (bottom-3), Weigh.Equally(short=True)
- [x] 2.2 Create `examples/15_vix_regime_switching.py` — Signal.VIX with low_vol and high_vol child portfolios
