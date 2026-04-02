## ADDED Requirements

### Requirement: Signal.Indicator accepts a condition function and lookback window
`Signal.Indicator` SHALL accept:
- `condition: Callable[[pd.Series], bool]` — receives a Series of close prices over the lookback window, returns a boolean state.
- `lookback: pd.DateOffset` — defines how far back from `context.date` to slice prices.
- `ticker: str` — which ticker's prices to evaluate the condition against.
- `cross: str` — one of `"up"`, `"down"`, or `"both"`. Default `"up"`.

#### Scenario: Constructor accepts all parameters
- **WHEN** `Signal.Indicator(ticker="QQQ", condition=fn, lookback=pd.DateOffset(days=200), cross="up")` is created
- **THEN** the algo SHALL store the parameters without error

#### Scenario: Invalid cross value raises
- **WHEN** `Signal.Indicator(ticker="QQQ", condition=fn, lookback=pd.DateOffset(days=200), cross="invalid")` is created
- **THEN** a `ValueError` SHALL be raised

### Requirement: Condition receives lookback window of close prices
On each call, the algo SHALL slice `context.prices[ticker].loc[start:end, "close"]` where `start = context.date - lookback` and `end = context.date`, then pass the resulting Series to the condition function.

#### Scenario: Condition receives correct price window
- **WHEN** the algo is called with `lookback=pd.DateOffset(days=50)` and `context.date` is 2023-06-15
- **THEN** the condition function SHALL receive close prices from approximately 2023-04-26 through 2023-06-15

#### Scenario: Insufficient price data
- **WHEN** the lookback window extends before the earliest available price
- **THEN** the algo SHALL pass whatever prices are available (partial window) and let the condition function decide

### Requirement: Edge detection fires only on state transitions
The algo SHALL track the previous boolean state returned by the condition function. It SHALL fire True (return True) only when the state **transitions**:
- `cross="up"`: fire on False → True transition only
- `cross="down"`: fire on True → False transition only
- `cross="both"`: fire on any state change (False→True or True→False)

#### Scenario: Cross up detection
- **WHEN** `cross="up"` and the previous state was False and current state is True
- **THEN** the algo SHALL return True

#### Scenario: Cross up does not fire on steady True
- **WHEN** `cross="up"` and the previous state was True and current state is True
- **THEN** the algo SHALL return False

#### Scenario: Cross down detection
- **WHEN** `cross="down"` and the previous state was True and current state is False
- **THEN** the algo SHALL return True

#### Scenario: Cross both detection
- **WHEN** `cross="both"` and the state changes in either direction
- **THEN** the algo SHALL return True

#### Scenario: No transition means no fire
- **WHEN** the state is the same as the previous bar (True→True or False→False)
- **THEN** the algo SHALL return False regardless of `cross` setting

### Requirement: First bar initialises state without firing
On the first call (no previous state), the algo SHALL evaluate the condition to set the initial state but SHALL NOT fire True.

#### Scenario: First bar never fires
- **WHEN** the algo is called for the first time
- **THEN** it SHALL return False and store the current condition result as the initial state

### Requirement: Composable with existing pipeline
`Signal.Indicator` SHALL be usable in any position where a Signal algo is expected, including inside `Or(...)` combinators.

#### Scenario: Combined with calendar signal via Or
- **WHEN** `Or(Signal.Monthly(), Signal.Indicator(...))` is used
- **THEN** rebalancing SHALL occur on either monthly schedule or indicator crossover

#### Scenario: Used as sole signal in algo queue
- **WHEN** `Signal.Indicator(...)` is the only signal in a portfolio's algo stack
- **THEN** the portfolio SHALL rebalance only on crossover bars
