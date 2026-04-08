## ADDED Requirements

### Requirement: Skill triggers on backtesting requests
The skill SHALL trigger when users ask to backtest, simulate, or evaluate asset allocation strategies, portfolio strategies, or rebalancing approaches.

#### Scenario: Direct backtest request
- **WHEN** user says "backtest 60/40 QQQ BIL monthly rebalance from 2019 to 2024"
- **THEN** the skill activates and converts the request into a tiportfolio CLI command

#### Scenario: Strategy evaluation request
- **WHEN** user says "how would equal weight QQQ BIL GLD perform with monthly rebalancing?"
- **THEN** the skill activates and runs a backtest

#### Scenario: Non-backtest request ignored
- **WHEN** user asks a general coding question unrelated to portfolio backtesting
- **THEN** the skill does NOT activate

### Requirement: Auto-install tiportfolio if not present
The skill SHALL check if `tiportfolio` is available and install it via `uvx install tiportfolio` if not found.

#### Scenario: tiportfolio not installed
- **WHEN** `tiportfolio --help` fails (command not found)
- **THEN** the skill runs `uvx install tiportfolio` before proceeding

#### Scenario: tiportfolio already installed
- **WHEN** `tiportfolio --help` succeeds
- **THEN** the skill proceeds directly to building the CLI command

### Requirement: Map natural language to CLI flags
The skill SHALL extract parameters from the user's request and map them to tiportfolio CLI flags.

#### Scenario: Basic backtest mapping
- **WHEN** user says "backtest QQQ BIL GLD equal weight monthly from 2019-01-01 to 2024-12-31"
- **THEN** the skill builds: `tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal`

#### Scenario: Custom ratio mapping
- **WHEN** user says "70/20/10 allocation of QQQ BIL GLD quarterly"
- **THEN** the skill builds: `tiportfolio quarterly --tickers QQQ,BIL,GLD --ratio 0.7,0.2,0.1 --start <default> --end <default>`

#### Scenario: AIP mapping
- **WHEN** user says "monthly $1000 DCA into QQQ BIL GLD equal weight"
- **THEN** the skill builds: `tiportfolio monthly --tickers QQQ,BIL,GLD --ratio equal --aip 1000 --start <default> --end <default>`

#### Scenario: Leverage mapping
- **WHEN** user says "compare 1x vs 1.5x vs 2x leverage on monthly QQQ BIL GLD"
- **THEN** the skill builds: `tiportfolio monthly --tickers QQQ,BIL,GLD --ratio equal --leverage 1.0,1.5,2.0 --start <default> --end <default>`

### Requirement: Run command and present results
The skill SHALL execute the built CLI command via Bash and present the results clearly to the user.

#### Scenario: Successful backtest
- **WHEN** the tiportfolio CLI command completes successfully
- **THEN** the skill presents the summary table and offers to show full summary or save a chart

#### Scenario: Command fails
- **WHEN** the CLI command fails (e.g., invalid tickers, missing data)
- **THEN** the skill presents the error and suggests corrections

### Requirement: Default date range
The skill SHALL use sensible defaults when the user omits start/end dates.

#### Scenario: No dates specified
- **WHEN** user says "backtest QQQ BIL GLD monthly equal weight" without dates
- **THEN** the skill uses a default range (e.g., last 5 years from today)
