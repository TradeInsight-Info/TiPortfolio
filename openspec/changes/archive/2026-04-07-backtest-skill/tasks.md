> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [x]) syntax for tracking.

## 1. Plugin Manifest

- [x] 1.1 Create `.claude-plugin/marketplace.json` with plugin name "tiportfolio" and skill path `./skills/backtest`

## 2. Skill File

- [x] 2.1 Create `skills/backtest/SKILL.md` with frontmatter: name (`backtest`), description (trigger on backtesting, portfolio strategy, asset allocation, DCA, rebalancing requests)
- [x] 2.2 Add installation check section: run `tiportfolio --help`, if fails run `uvx install tiportfolio`, if still fails suggest `pip install tiportfolio`
- [x] 2.3 Add parameter mapping table and extraction instructions (tickers, dates, frequency, ratio, AIP, leverage, plot, full)
- [x] 2.4 Add default values section: default frequency=monthly, default ratio=equal, default date range=5 years ago to today
- [x] 2.5 Add 5+ example mappings showing natural language → CLI command
- [x] 2.6 Add execution instructions: show the command to user, run it via Bash, present summary, offer follow-ups (full summary, chart)
- [x] 2.7 Add error handling instructions: if command fails, show error, suggest fixes

## 3. Verify

- [x] 3.1 Verify marketplace.json is valid JSON and SKILL.md has valid YAML frontmatter
