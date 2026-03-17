# Allocation & Engine Design Review

Date: 2026-03-18
Scope: `src/tiportfolio/allocation/`, `src/tiportfolio/engine/`
Purpose: Reference for future design decisions — issues and improvement ideas, not action items.

---

## Bugs / Dead Code

### 1. `schedule_kwargs` is never used — `engine/volatility.py`

`schedule_kwargs` is populated inside `VolatilityBasedEngine.run()` when `self.rebalance.spec == "vix_regime"` but is never passed to any function. The `get_rebalance_dates()` call below it passes its own arguments directly. Safe to remove entirely.

### 2. `lower_thresh` is computed but never used — `engine/volatility.py`

Inside the `context_for_date` closure:
```python
upper_thresh = target_vix + upper_bound
lower_thresh = target_vix + lower_bound   # ← computed, never read
use_high_vol = vix_value >= upper_thresh
```
`lower_thresh` has no effect. Either the hysteresis logic (enter high-vol above `upper_thresh`, exit below `lower_thresh`) was intended but not implemented, or this is leftover from an earlier design. Flag for intentional decision.

---

## ABC Consistency

### 3. `_AllocationWrapper` bypasses the `AllocationStrategy` ABC — `engine/volatility.py`

`_AllocationWrapper` is an internal workaround that wraps an allocation to inject modified `get_target_weights` behaviour. It implements `get_symbols` and `get_target_weights` but does **not** inherit `AllocationStrategy`. This creates an internal inconsistency: the engine's own code violates the ABC rule we enforce on user-facing strategies.

If `run_backtest()` or any future code ever does `isinstance(allocation, AllocationStrategy)`, this will fail silently or raise. Options:
- Make `_AllocationWrapper` inherit `AllocationStrategy` (requires making it a proper dataclass or implementing `__post_init__`-style init)
- Keep it private and accept the inconsistency explicitly with a comment
- Replace the wrapper pattern with a different injection mechanism (e.g., a subclass of the original allocation)

### 4. `BacktestEngine` declares no `@abstractmethod` — `engine/base.py`

`BacktestEngine(ABC)` has a concrete `run()` implementation that subclasses override entirely. There is no `@abstractmethod`, so the ABC label is misleading — Python will not prevent instantiating `BacktestEngine` directly. Either:
- Remove the ABC inheritance (it's a concrete base class)
- Declare an abstract `_run_impl()` or `_fetch_prices()` that subclasses must implement, restructuring the inheritance properly

---

## API Discoverability

### 5. `**context` keys are implicit — `allocation/base.py`

The `get_target_weights` ABC declares `**context: Any`, but the keys injected by the engine (`vix_at_date`, `use_high_vol_allocation`, `prices_history`, `signal_date`, `last_rebalance_date`) are not declared anywhere in the ABC. A user implementing a custom strategy must read `engine/volatility.py` and `backtest.py` to discover what's available.

Options:
- Add a `StrategyContext` typed dataclass or `TypedDict` documenting all keys
- Document available keys as a class-level docstring on `AllocationStrategy`
- Keep `**context` but add a reference in the ABC docstring pointing to the engine docs

### 6. `VixRegimeAllocation` is silently broken with `ScheduleBasedEngine`

`VixRegimeAllocation.get_target_weights()` reads `context.get("use_high_vol_allocation", False)`. When used with `ScheduleBasedEngine` (which never injects this key), it silently always uses `low_vol_allocation`. There is no guard, warning, or documentation that this combination is unsupported.

Options:
- Add a `__post_init__` check that is engine-agnostic (not possible without circular dep)
- Emit a `warnings.warn()` in `get_target_weights` when context is empty or missing the key
- Document the coupling explicitly in the class docstring

### 7. `rebalance_filter` has no formal interface

`VolatilityBasedEngine.run()` accepts `rebalance_filter: Callable[[pd.Timestamp, pd.Series, pd.Timestamp | None], bool] | None`. Users who want to implement a custom filter have no ABC, no helper class, and no examples (outside test files). `VixChangeFilter` exists but isn't discoverable as the reference implementation from the type hint alone.

Options:
- Add `RebalanceFilter` as an ABC alongside `AllocationStrategy`
- At minimum, add a docstring reference to `VixChangeFilter` as the example implementation

---

## Engine API Complexity

### 8. `VolatilityBasedEngine.run()` has too many parameters

The `run()` signature has 9 parameters. Several (`target_vix`, `lower_bound`, `upper_bound`) are only meaningful when `rebalance == "vix_regime"`. Passing them with other schedules has no effect, which is confusing.

Options:
- Introduce a `VixRegimeConfig` dataclass that bundles the VIX-regime-specific params, passed as a single optional argument
- Validate at call time and raise `ValueError` if VIX params are passed with a non-vix schedule
- Split into two engine subclasses: one for `rebalance_filter`-based engines and one for `vix_regime`

### 9. Engine selection is non-obvious

The three engine classes share the same constructor but differ in what `run()` accepts (prices dict vs symbols list). A new user reading the public API can't tell which to use without reading the class docstrings. The hierarchy (`BacktestEngine` → `ScheduleBasedEngine`, `VolatilityBasedEngine`) implies `VolatilityBasedEngine` is an extension of `ScheduleBasedEngine`, but they are actually siblings. The naming doesn't communicate this.

---

## Minor / Cleanup

### 10. `validate_vix_regime_bounds` is in the public `__all__` — `allocation/__init__.py`

This is an internal validation helper. Exporting it from the package's `__all__` bloats the public API surface. Consider removing from `__all__` and prefixing with `_`.

### 11. Source-level CLAUDE.md stale after engine refactor

`src/tiportfolio/CLAUDE.md` (the inner project CLAUDE) still refers to `engine.py` rather than `engine/`. Low priority but misleads agents reading architecture docs.

### 12. `get_target_weights` positional parameter weight

The 4 mandatory positional params (`date`, `total_equity`, `positions_dollars`, `prices_row`) must be accepted by every strategy even when unused (e.g., `FixRatio` ignores all four). This is the standard visitor/callback pattern tradeoff — no strong action needed, but worth noting if the interface is revisited. Keyword-only parameters with defaults would reduce the implementation burden for simple strategies.

---

## Summary Table

| # | Category | Severity | File | Done |
|---|----------|----------|------|------|
| 1 | Dead code | Low | `engine/volatility.py` | ☐ |
| 2 | Dead code / unclear intent | Medium | `engine/volatility.py` | ☐ |
| 3 | ABC consistency | Medium | `engine/volatility.py` | ☑ |
| 4 | ABC misleading | Low | `engine/base.py` | ☑ |
| 5 | Discoverability | Medium | `allocation/base.py` | ☑ |
| 6 | Silent wrong behavior | High | `allocation/vix.py` | ☑ |
| 7 | Missing interface | Low | `engine/volatility.py` | ☑ |
| 8 | API complexity | Medium | `engine/volatility.py` | ☑ |
| 9 | Naming / discoverability | Low | `engine/` | ☑ |
| 10 | API bloat | Low | `allocation/__init__.py` | ☐ |
| 11 | Stale docs | Low | `src/tiportfolio/CLAUDE.md` | ☑ |
| 12 | Interface ergonomics | Low | `allocation/base.py` | ☐ |
