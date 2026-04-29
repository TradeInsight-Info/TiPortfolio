---
name: Architectural Decisions
description: Key design decisions made during TiPortfolio development — why things are the way they are
type: project
---

# Architectural Decisions

## Algo Stack Pipeline Pattern

**Decision**: All strategy logic is decomposed into three composable stages: `Signal` (when to rebalance) → `Select` (which assets to hold) → `Weigh` (how much of each).

**Why**: Separates the three orthogonal concerns of portfolio construction. Each stage can be swapped independently — e.g., change `Weigh.Equal` to `Weigh.ERC` without touching signal or selection logic. Maps naturally to how practitioners think about portfolio design.

**How to apply**: When adding a new strategy, always identify which stage it belongs to. Never put weighting logic in a Signal class or selection logic in a Weigh class.

---

## ABC over Protocol for Interfaces

**Decision**: All strategy implementations must explicitly inherit from their ABC (`Signal`, `Select`, `Weigh`, etc.). `Protocol`-based duck typing is explicitly prohibited.

**Why**: Enforces the contract at class definition time, not at call time. Makes the inheritance hierarchy visible in IDEs and static analysis. Prevents accidental partial implementations that pass duck-type checks.

**How to apply**: Every new algo class must have `class MySignal(Signal.Base):` or equivalent ABC parent. Do not use `typing.Protocol`.

---

## Parent-Child Portfolio Engine for Regime Switching

**Decision**: Regime-switching strategies (e.g., VIX-based) use a parent `Portfolio` that holds child `Portfolio` objects. The parent's Signal algo selects which child is active and writes its weight.

**Why**: Enables arbitrarily nested strategy trees without special-casing regime logic in the engine. A regime switch is just a `Select` operation at the parent level. This composability means complex strategies (VIX regime + beta-neutral child) are assembled from simple primitives.

**How to apply**: When implementing regime switching, use `Portfolio(children=[low_vol_p, high_vol_p])` with a regime `Signal`. Do not add regime flags to the engine core.

---

## run_aip is Month-End Only (for now)

**Decision**: `run_aip()` injects cash only on the last trading day of each calendar month. Frequency and trigger-date parameters are planned but not yet implemented.

**Why**: Simplest correct implementation for the most common AIP use case (monthly DCA). Extensibility was deferred to keep the initial implementation focused.

**How to apply**: When users ask about weekly or custom-frequency AIP, note this is planned. Do not add frequency logic to `run_aip()` until the spec is written.

---

## CLI as Consumer of Python API (Not Replacement)

**Decision**: The `tiportfolio` CLI is a thin wrapper over the Python API. No business logic lives in `cli.py` — it only maps flags to API calls.

**Why**: Prevents divergence between Python and CLI behavior. The Python API remains the source of truth; the CLI is just an ergonomic entry point.

**How to apply**: When adding CLI flags, find the corresponding Python API parameter. If the parameter doesn't exist in the Python API, add it there first.

---

## Offline Testing via Local CSV Fixtures

**Decision**: All tests use local CSV files in `tests/data/` (via `prices_three`, `prices_dict` fixtures from `conftest.py`). No test should make network calls to yfinance or any external source.

**Why**: Network calls make tests non-reproducible, slow, and fragile. A test suite that hits yfinance will fail during CI rate-limiting or market holidays.

**How to apply**: Any new test that needs price data must use the fixture CSVs. If new tickers are needed, add them to `tests/data/` — do not add `download()` calls to tests.

---

## Spec-Driven Development via openspec

**Decision**: All features are specified in `openspec/specs/<capability>/spec.md` before implementation. Completed change proposals live in `openspec/changes/archive/`.

**Why**: Provides a behavioral contract that survives refactors. The spec is the source of truth for what a capability must do — tests are derived from the spec scenarios.

**How to apply**: When asked to implement a feature, check `openspec/specs/<name>/spec.md` first. Implement the spec scenarios as test cases before writing production code.
