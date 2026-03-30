## ADDED Requirements

### Requirement: Signal.VIX switches between two child portfolios based on VIX level
`Signal.VIX` SHALL accept `high: float`, `low: float`, and `data: dict[str, pd.DataFrame]` (must contain `"^VIX"`). It SHALL write to both `context.selected` and `context.weights`.

#### Scenario: VIX below low threshold
- **WHEN** VIX close is 18 and `low=20`
- **THEN** `context.selected = [children[0]]` (low-vol regime) and `context.weights = {children[0].name: 1.0}`

#### Scenario: VIX above high threshold
- **WHEN** VIX close is 35 and `high=30`
- **THEN** `context.selected = [children[1]]` (high-vol regime) and `context.weights = {children[1].name: 1.0}`

#### Scenario: VIX between thresholds (hysteresis)
- **WHEN** VIX close is 25 (between low=20 and high=30) and previous selection was children[0]
- **THEN** `context.selected = [children[0]]` (persists previous selection)

### Requirement: Signal.VIX lazy initialisation defaults to low-vol
On the first call, `_active` SHALL default to `portfolio.children[0]` (low-vol regime).

#### Scenario: First call with VIX=25 (between thresholds)
- **WHEN** Signal.VIX is called for the first time with VIX between thresholds
- **THEN** it selects `children[0]` (default low-vol)

### Requirement: Signal.VIX children ordering contract
`portfolio.children[0]` SHALL be the low-vol (risk-on) portfolio. `portfolio.children[1]` SHALL be the high-vol (risk-off) portfolio.

#### Scenario: Correct ordering
- **WHEN** parent is constructed as `Portfolio('regime', algos, [low_vol, high_vol])`
- **THEN** VIX < low activates `low_vol`, VIX > high activates `high_vol`

### Requirement: Signal.VIX always returns True
`Signal.VIX.__call__` SHALL always return `True` to allow the algo queue to continue.

#### Scenario: Always continues
- **WHEN** Signal.VIX is called
- **THEN** it returns `True`
