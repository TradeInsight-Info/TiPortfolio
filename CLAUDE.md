- Follow [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and project structure details.


## Code Style

### General Principles

- **Python 3.12 target**, compatible with 3.10+
- **Simplicity first**: prefer fewer files/classes unless complexity is justified
- **TDD approach**: write/update tests first, then implement
- **Keep changes simple**: reuse existing utilities before writing new ones

### Type Annotations

- All functions must have type annotations on parameters and return types
- Use built-in types (`list[str]`, `dict[str, float]`); use `Any` when type cannot be specified

### Naming Conventions

- **Classes**: `PascalCase` — **Functions/methods**: `snake_case` — **Constants**: `UPPER_SNAKE_CASE`
- **Modules**: `snake_case` — **Private**: `_prefix`

### Imports

- Absolute imports from package root; grouped: stdlib → third-party → local; sorted alphabetically

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from tiportfolio.calendar import Schedule
```

### Docstrings

- Google-style for public APIs; include Args, Returns, Raises when applicable

### Error Handling

- Prefer built-in exceptions; validate inputs early
- `ValueError` for invalid arguments, `TypeError` for wrong types

### Data Classes

- Use `@dataclass` for data containers; use `__post_init__` for validation

### Abstract Base Classes

- Use `ABC` and `@abstractmethod` for interfaces — **no duck typing via `Protocol`**
- All strategy implementations must explicitly inherit from their ABC
- Name ABCs with `Strategy` suffix (e.g., `AllocationStrategy`)

### Testing Conventions

- Test files: `test_<module>.py`; use fixtures from `conftest.py` to avoid network calls
- Use local CSV files in `tests/data/` for offline testing; key fixtures: `prices_three`, `prices_dict`