## ADDED Requirements

### Requirement: Or combinator returns True when any inner algo returns True
The `Or` class SHALL be an `Algo` subclass that accepts `*algos: Algo` and returns `True` when any inner algo returns `True`. It SHALL short-circuit on the first `True` (later algos do not execute).

#### Scenario: All inner algos return False
- **WHEN** `Or(algo_false_1, algo_false_2)` is called
- **THEN** result is `False` and both algos were called

#### Scenario: First algo returns True
- **WHEN** `Or(algo_true, algo_false)` is called
- **THEN** result is `True` and only the first algo was called (short-circuit)

#### Scenario: Second algo returns True
- **WHEN** `Or(algo_false, algo_true)` is called
- **THEN** result is `True` and both algos were called

### Requirement: And combinator returns True when all inner algos return True
The `And` class SHALL be an `Algo` subclass that accepts `*algos: Algo` and returns `True` only when all inner algos return `True`. It SHALL short-circuit on the first `False`.

#### Scenario: All inner algos return True
- **WHEN** `And(algo_true_1, algo_true_2)` is called
- **THEN** result is `True` and both algos were called

#### Scenario: First algo returns False
- **WHEN** `And(algo_false, algo_true)` is called
- **THEN** result is `False` and only the first algo was called (short-circuit)

### Requirement: Not combinator inverts a single algo result
The `Not` class SHALL be an `Algo` subclass that accepts a single `algo: Algo` and returns the opposite boolean value.

#### Scenario: Inner algo returns True
- **WHEN** `Not(algo_true)` is called
- **THEN** result is `False`

#### Scenario: Inner algo returns False
- **WHEN** `Not(algo_false)` is called
- **THEN** result is `True`

### Requirement: Combinators are exported at ti.* level
`Or`, `And`, `Not` SHALL be importable as `ti.Or`, `ti.And`, `ti.Not` from the `tiportfolio` package.

#### Scenario: Public import
- **WHEN** user writes `import tiportfolio as ti`
- **THEN** `ti.Or`, `ti.And`, `ti.Not` are accessible and are `Algo` subclasses

### Requirement: Combinators support nesting
Combinators SHALL accept other combinators as inner algos for arbitrary composition.

#### Scenario: Nested composition
- **WHEN** `Or(And(algo_true, algo_false), Not(algo_false))` is called
- **THEN** result is `True` (`And` returns `False`, `Not` returns `True`, `Or` short-circuits on second)
