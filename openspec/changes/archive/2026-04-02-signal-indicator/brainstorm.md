# Signal.Indicator — Technical Analysis Signal Algo

**Goal**: Add a `Signal.Indicator` algo that fires on indicator state transitions (crossovers, threshold breaches), enabling TA-based strategies like SMA crossover.
**Architecture**: New `Algo` subclass in `signal.py` that computes indicators from price history on each bar and fires True only on state *transitions* (edge detection), not on static state.
**Tech Stack**: Python 3.12, pandas (rolling windows), existing `Algo`/`Context` framework
**Spec**: `openspec/changes/signal-indicator/specs/`

## File Map:

1. Modify : `src/tiportfolio/algos/signal.py` - Add `Signal.Indicator` class
2. Modify : `src/tiportfolio/algos/__init__.py` - Ensure `Signal.Indicator` is exported (already via namespace class)
3. Create : `tests/test_signal_indicator.py` - Unit tests for the new algo
4. Modify : `examples/` - Add an SMA crossover example (optional)

## Chunks

### Chunk 1: Core Signal.Indicator algo
The main algo class that accepts a user-defined condition function operating on a price lookback window. Key design insight: the condition function returns a boolean *state* (e.g., SMA50 > SMA200), but the algo fires True only when that state **transitions** from False→True (cross up) or True→False (cross down), depending on configuration.

Files:
- `src/tiportfolio/algos/signal.py`

Steps:
- Step 1: Define `Signal.Indicator` class with params: `condition: Callable[[pd.Series], bool]`, `lookback: pd.DateOffset`, `cross: "up" | "down" | "both"`
- Step 2: In `__call__`, slice `context.prices` to `[date - lookback : date]`, pass close prices to condition
- Step 3: Track previous state (`self._prev_state`). Fire True only on transitions matching `cross` direction.
- Step 4: Handle first-bar edge case (no previous state → don't fire, just initialise)

### Chunk 2: Tests
Unit tests using synthetic price data to verify crossover edge detection.

Files:
- `tests/test_signal_indicator.py`

Steps:
- Step 1: Create synthetic prices with known SMA crossover points
- Step 2: Test that Indicator fires exactly on the crossover bar, not before or after
- Step 3: Test `cross="up"` only fires on False→True, `cross="down"` on True→False, `cross="both"` on either
- Step 4: Test first-bar initialisation (no spurious fire)
- Step 5: Test with insufficient lookback data (should not fire)
