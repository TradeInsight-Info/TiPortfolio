## Context

TiPortfolio examples follow a consistent pattern established in `examples/01_quick_start.py`:
1. `import _env` — loads `.env` for API keys
2. Define tickers and fetch data
3. Build a `ti.Portfolio` with an algo stack
4. `ti.run(ti.Backtest(...))` and print summary
5. Save chart to `examples/<name>.png`

All features needed by these examples are already implemented and tested. This change adds no new code.

## Goals / Non-Goals

**Goals:**
- One example per major Chunk 2–3 feature
- Each example is self-contained and runnable with `uv run python examples/<name>.py`
- Docstrings explain the strategy and which feature is being demonstrated
- Use the same 3-ETF universe (`QQQ`, `BIL`, `GLD`) where possible for consistency

**Non-Goals:**
- No testing of examples (they hit external APIs for data)
- No example for `Select.Filter` (requires external condition data — better as a doc recipe)
- No example for `Signal.EveryNPeriods` (covered by docstring, not distinct enough for its own script)
- No example for `Signal.Yearly` (similar to Quarterly; low incremental value)

## Decisions

### Example numbering: continue from 10

Continue the existing numbering sequence. Group Chunk 2 features (10–13, 16) before Chunk 3 features (14–15) to mirror the learning progression.

### Use allocation-strategies.md examples as reference

The `docs/guides/allocation-strategies.md` file contains reference implementations for dollar-neutral and volatility targeting. Example scripts should closely match these to maintain consistency between docs and examples.

## Risks / Trade-offs

- **[API rate limits]** → All examples call `ti.fetch_data` which hits YFinance. Users running many examples in sequence may get rate-limited. Mitigation: this is standard for example scripts.
