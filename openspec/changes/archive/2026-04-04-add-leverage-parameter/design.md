## Context

Currently `run(*tests: Backtest) -> BacktestResult` takes only `Backtest` objects. Leverage exists implicitly when algo weights sum > 1.0 (causing negative cash/borrowing). Users want an explicit, post-hoc leverage multiplier to compare strategies at different leverage levels without modifying portfolio definitions.

## Goals / Non-Goals

**Goals:**
- Add `leverage` keyword to `run()` with `float | list[float]` type, default `1.0`
- Apply leverage by scaling daily returns post-simulation, deducting borrowing cost using `config.loan_rate`
- Store leverage factor in results for display in summaries and portfolio naming
- Full backward compatibility — no existing code breaks

**Non-Goals:**
- Modifying the simulation engine (no changes to position sizing, mark-to-market, or carry costs)
- Modeling margin calls or liquidation
- Supporting time-varying leverage factors

## Decisions

### Decision 1: Post-simulation return scaling (not weight multiplication)

**Chosen**: Scale daily returns of the completed equity curve by the leverage factor, then rebuild.

**Alternative considered**: Multiply all weights by the leverage factor before simulation. This would model leverage more realistically (including carry costs on borrowed capital) but would require threading leverage through the algo queue and `execute_leaf_trades`, significantly increasing complexity.

**Rationale**: Post-simulation scaling is simple and predictable. Unlike pure synthetic scaling, we deduct borrowing costs using `config.loan_rate` to stay consistent with the engine's existing carry cost logic in `deduct_daily_carry_costs()`. This gives realistic leveraged performance without touching the simulation engine.

### Decision 2: Helper function `_apply_leverage()` in backtest.py

```python
def _apply_leverage(result: _SingleResult, factor: float, config: TiConfig) -> _SingleResult:
    eq = result.equity_curve
    returns = eq.pct_change().fillna(0.0)
    daily_borrow_cost = (factor - 1) * config.loan_rate / config.bars_per_year
    leveraged_returns = returns * factor - daily_borrow_cost
    leveraged_eq = eq.iloc[0] * (1 + leveraged_returns).cumprod()
    leveraged_eq.iloc[0] = eq.iloc[0]  # preserve initial capital
    # Return new _SingleResult with modified equity curve and leverage metadata
```

This keeps leverage logic isolated from the simulation engine.

### Decision 3: Leverage as keyword-only argument

`def run(*tests: Backtest, leverage: float | list[float] = 1.0)` — keyword-only because it follows `*tests`. This prevents accidental positional usage and keeps the API clean.

## Risks / Trade-offs

- **Borrowing cost uses a flat daily rate** → Does not model intraday margin or variable rates, but matches the engine's existing `deduct_daily_carry_costs()` approach for consistency.
- **Leverage can produce negative equity** (e.g., 3x on a -40% drawdown = -120%) → No mitigation needed; this correctly reflects leveraged risk. Summary metrics will show extreme drawdowns.
- **Name suffix changes may affect downstream code that matches on portfolio name** → Low risk; suffix only added when leverage != 1.0, and this is a new feature.
