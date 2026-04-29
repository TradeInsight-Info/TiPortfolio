---
name: Coding Patterns
description: Established coding patterns and conventions used consistently throughout TiPortfolio
type: project
---

# Coding Patterns

## Type Annotations — Built-in Generics

Use built-in generic types, not `typing` equivalents:

```python
# Correct
def run(backtests: list[Backtest], leverage: float | None = None) -> BacktestResult: ...

# Wrong — do not use
from typing import List, Optional
def run(backtests: List[Backtest], leverage: Optional[float] = None) -> BacktestResult: ...
```

Use `Any` when the type genuinely cannot be specified. Never use untyped parameters.

---

## Import Order

```python
from __future__ import annotations

# 1. stdlib
from dataclasses import dataclass
from typing import Any

# 2. third-party (alphabetical)
import pandas as pd
import numpy as np

# 3. local (absolute from package root, alphabetical)
from tiportfolio.engine import BacktestResult
from tiportfolio.portfolio import Portfolio
```

---

## Google-Style Docstrings (Public APIs Only)

```python
def run_aip(
    *backtests: Backtest,
    monthly_aip_amount: float,
    leverage: float | None = None,
) -> BacktestResult:
    """Run a backtest with periodic AIP cash injections.

    Args:
        backtests: One or more Backtest objects to simulate.
        monthly_aip_amount: Cash injected on the last trading day of each month.
        leverage: Optional leverage multiplier applied to the result.

    Returns:
        BacktestResult with equity curve, summary, and AIP-specific metrics.

    Raises:
        ValueError: If no backtests are provided or monthly_aip_amount <= 0.
    """
```

Internal helpers (`_prefixed`) do not need docstrings.

---

## ABC Pattern for Algo Strategies

```python
from abc import ABC, abstractmethod

class Signal(ABC):
    @abstractmethod
    def __call__(self, context: Context) -> None: ...

class Monthly(Signal):
    def __call__(self, context: Context) -> None:
        # implementation
```

All strategy classes inherit from their ABC. No `Protocol`-based duck typing.

---

## Test Structure

```python
# tests/test_<module>.py
import pytest
from tests.conftest import prices_three  # use shared fixtures

def test_run_aip_basic(prices_three):
    """Spec: run_aip returns BacktestResult with contribution metrics."""
    bt = Backtest(Portfolio(...), prices_three)
    result = run_aip(bt, monthly_aip_amount=1000)
    assert "total_contributions" in result.summary().index
    assert "contribution_count" in result.summary().index
```

- One test file per module: `test_engine.py`, `test_cli.py`, etc.
- Use `prices_three` / `prices_dict` fixtures from `conftest.py` — never `yf.download()` in tests.
- Test names describe the behavior being tested, not the method name.

---

## Error Handling — Early Validation

```python
def run_aip(*backtests: Backtest, monthly_aip_amount: float) -> BacktestResult:
    if not backtests:
        raise ValueError("At least one Backtest is required")
    if monthly_aip_amount <= 0:
        raise ValueError(f"monthly_aip_amount must be positive, got {monthly_aip_amount}")
```

Validate at public API boundaries. Trust internal invariants. Use `ValueError` for bad arguments, `TypeError` for wrong types.

---

## DataFrame Column Normalization

Always lowercase column names when receiving external data:

```python
df.columns = df.columns.str.lower()
```

Canonical OHLCV columns: `open`, `close`, `high`, `low`, `volume`. Internal code always uses lowercase.

---

## Constants and Configuration

```python
# Module-level constants in UPPER_SNAKE_CASE
DEFAULT_CAPITAL = 100_000.0
DEFAULT_FEE = 0.001
RISK_FREE_RATE = 0.0
```

Never hardcode magic numbers inline. Always define a named constant at module scope.
