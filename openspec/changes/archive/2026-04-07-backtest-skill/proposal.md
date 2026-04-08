## Why

Users of Claude Code often want to quickly test "what if I did 60/40 QQQ/BIL monthly rebalance?" without remembering CLI syntax. A marketplace skill bridges the gap — users install the plugin, describe their strategy in plain English, Claude maps it to `tiportfolio` CLI commands, runs the backtest, and presents results. If tiportfolio isn't installed, the skill auto-installs it via `uvx`.

Publishing as a Claude Code marketplace plugin (following the vercel-labs/skills pattern) makes the skill discoverable and installable by anyone.

## What Changes

- Create `.claude-plugin/marketplace.json` — plugin manifest exposing the skill to the Claude Code marketplace
- Create `skills/backtest/SKILL.md` — the skill definition
- Skill triggers on backtesting, asset allocation, portfolio strategy requests
- Auto-installs `tiportfolio` via `uvx install tiportfolio` if not found
- Maps natural language to tiportfolio CLI flags (tickers, dates, frequency, ratio, AIP, leverage, plot)
- Runs the CLI command and presents summary + chart

## Capabilities

### New Capabilities
- `backtest-skill`: Claude Code marketplace plugin with a backtest skill that converts natural language backtesting requests into tiportfolio CLI commands, auto-installing the tool if needed

### Modified Capabilities
_None_

## Impact

- **Code**: 2 new files — `.claude-plugin/marketplace.json` and `skills/backtest/SKILL.md`
- **APIs**: No library changes
- **Dependencies**: Relies on `tiportfolio` CLI (auto-installed via uvx)
- **Distribution**: Published to Claude Code marketplace via `.claude-plugin/marketplace.json`
