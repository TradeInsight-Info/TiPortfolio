## ADDED Requirements

### Requirement: TiConfig dataclass holds simulation parameters
The system SHALL provide a `TiConfig` frozen dataclass with fields: `fee_per_share` (float, default 0.0035), `risk_free_rate` (float, default 0.04), `loan_rate` (float, default 0.0514), `stock_borrow_rate` (float, default 0.07), `initial_capital` (float, default 10_000), `bars_per_year` (int, default 252).

#### Scenario: Default TiConfig
- **WHEN** `TiConfig()` is constructed with no arguments
- **THEN** all fields have their documented default values

#### Scenario: Custom TiConfig
- **WHEN** `TiConfig(fee_per_share=0.01, initial_capital=50_000)` is constructed
- **THEN** the specified fields override defaults; unspecified fields keep defaults

### Requirement: Context dataclass carries algo communication
The system SHALL provide a `Context` dataclass with read-only fields (`portfolio`, `prices`, `date`, `config`) and mutable fields (`selected`, `weights`). It SHALL also carry engine callbacks `_execute_leaf` and `_allocate_children`.

#### Scenario: Context construction
- **WHEN** a Context is created with a portfolio, prices dict, date, and config
- **THEN** `selected` defaults to empty list, `weights` defaults to empty dict, callbacks default to None

#### Scenario: Algos mutate context.selected and context.weights
- **WHEN** an algo writes `context.selected = ["QQQ"]` and `context.weights = {"QQQ": 1.0}`
- **THEN** subsequent algos in the queue can read those values

### Requirement: Algo ABC defines the algo contract
The system SHALL provide an abstract base class `Algo` with a single abstract method `__call__(self, context: Context) -> bool`. Returning `True` continues the queue; `False` aborts.

#### Scenario: Algo subclass must implement __call__
- **WHEN** a class inherits from `Algo` without implementing `__call__`
- **THEN** instantiation raises `TypeError`

### Requirement: AlgoQueue executes algos sequentially with short-circuit
The system SHALL provide `AlgoQueue(Algo)` that takes a list of algos and runs them in order. It SHALL short-circuit on the first `False` return — remaining algos do not execute.

#### Scenario: All algos return True
- **WHEN** an AlgoQueue of 3 algos that all return True is called
- **THEN** all 3 algos execute and AlgoQueue returns True

#### Scenario: Second algo returns False
- **WHEN** an AlgoQueue of 3 algos where the second returns False is called
- **THEN** only the first 2 algos execute, the third does not, and AlgoQueue returns False

### Requirement: Portfolio holds mutable simulation state
The system SHALL provide a `Portfolio` class with: `name` (str), `algo_queue` (AlgoQueue, built from user's algos list), `children` (list[str] | list[Portfolio] | None), and mutable state: `positions` (dict[str, float]), `cash` (float), `equity` (float).

#### Scenario: Leaf portfolio construction
- **WHEN** `Portfolio("test", [algo1, algo2], ["QQQ", "BIL"])` is constructed
- **THEN** `name` is "test", `children` is ["QQQ", "BIL"], `algo_queue` wraps the algos in an AlgoQueue, and `positions` is `{}`, `cash` is `0.0`, `equity` is `0.0`

#### Scenario: Portfolio state is mutable
- **WHEN** engine sets `portfolio.cash = 10_000` and `portfolio.positions = {"QQQ": 50.0}`
- **THEN** those values persist on the portfolio object across bars
