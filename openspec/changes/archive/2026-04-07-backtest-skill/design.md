## Context

Claude Code marketplace plugins follow the vercel-labs/skills pattern:
- `.claude-plugin/marketplace.json` at repo root declares the plugin and its skills
- Skills live in `skills/<name>/SKILL.md` with YAML frontmatter and Markdown body
- The runtime discovers skills via the manifest paths

TiPortfolio's CLI supports: `monthly`, `quarterly`, `weekly`, `yearly`, `every`, `once` subcommands with `--tickers`, `--start`, `--end`, `--ratio`, `--select`, `--leverage`, `--aip`, `--plot`, `--full`, `--csv` flags.

## Goals / Non-Goals

**Goals:**
- Create a marketplace plugin with a backtest skill
- Map natural language backtesting requests to tiportfolio CLI commands
- Auto-install tiportfolio via uvx if not present
- Support all major CLI features: frequency, ratio, AIP, leverage, plot

**Non-Goals:**
- Python library usage (this skill uses CLI only)
- Advanced strategy composition (VIX signals, beta-neutral, etc.) — future skill
- Interactive chart rendering (CLI outputs matplotlib PNGs)

## Decisions

### 1. Plugin structure

```
TiPortfolio/
├── .claude-plugin/
│   └── marketplace.json
└── skills/
    └── backtest/
        └── SKILL.md
```

**marketplace.json:**
```json
{
  "metadata": {},
  "plugins": [
    {
      "name": "tiportfolio",
      "skills": ["./skills/backtest"]
    }
  ]
}
```

No `pluginRoot` needed — skills are at repo root level. The plugin name is `tiportfolio` so skills appear as `tiportfolio:backtest`.

### 2. Auto-install approach

Check with `tiportfolio --help` first. If not found, run `uvx install tiportfolio`. If uvx fails, suggest `pip install tiportfolio`.

### 3. Parameter mapping strategy

The skill body contains a **mapping table** that Claude uses to convert natural language to CLI flags:

| User intent | CLI flag | Default |
|---|---|---|
| Tickers/assets | `--tickers QQQ,BIL,GLD` | (required — ask if missing) |
| Start date | `--start 2019-01-01` | 5 years ago |
| End date | `--end 2024-12-31` | today |
| Frequency | subcommand: monthly/quarterly/weekly/yearly/once | `monthly` |
| Equal weight | `--ratio equal` | `equal` |
| Custom ratio: 60/40, 70/20/10 | `--ratio 0.6,0.4` | — |
| ERC / risk parity | `--ratio erc` | — |
| AIP/DCA amount | `--aip 1000` | — |
| Leverage | `--leverage 1.5` | — |
| Compare leverage | `--leverage 1.0,1.5,2.0` | — |
| Full summary | `--full` | off |
| Save chart | `--plot <path>` | — |

Plus **example mappings** showing input → command.

### 4. Result presentation

After running, the skill instructs Claude to:
1. Show the summary table from stdout
2. Offer: "Want the full summary?" or "Save a chart?"
3. If fails, explain error and suggest fixes

### 5. Default date range

When user omits dates, compute dynamically: 5 years ago → today.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| uvx not available on all systems | Fallback: suggest `pip install tiportfolio` |
| Natural language ambiguity | Show the constructed command before running so user can verify |
| Missing tickers | Ask user — tickers are the only required parameter |
