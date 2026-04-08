# Backtest Skill for Claude Code Marketplace

**Goal**: Create a Claude Code marketplace plugin exposing a `backtest` skill that lets users backtest asset allocation strategies via natural language, converting requests into `tiportfolio` CLI commands.
**Architecture**: A marketplace plugin at repo root with `.claude-plugin/marketplace.json` pointing to `skills/backtest/SKILL.md`. Published to Claude Code marketplace via the vercel-labs/skills pattern.
**Tech Stack**: Claude Code plugin system (marketplace.json + SKILL.md), tiportfolio CLI, uvx for installation
**Spec**: `openspec/specs/backtest-skill/spec.md`

## File Map:

1. Create : `.claude-plugin/marketplace.json` - Plugin manifest exposing the backtest skill
2. Create : `skills/backtest/SKILL.md` - The skill definition with trigger description, installation check, parameter mapping, and execution instructions

## Chunks

### Chunk 1: Create plugin manifest and skill file

Files:
- `.claude-plugin/marketplace.json`
- `skills/backtest/SKILL.md`
Steps:
- Step 1: Create marketplace.json with plugin name "tiportfolio" and skill path "./skills/backtest"
- Step 2: Write SKILL.md with frontmatter (name, description for triggering)
- Step 3: Body: installation check logic (uvx install tiportfolio if `tiportfolio --help` fails)
- Step 4: Body: parameter mapping table (natural language → CLI flags)
- Step 5: Body: examples showing input → CLI command → output pattern
- Step 6: Body: instructions for running the command and presenting results
