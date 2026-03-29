# Cleanup + Buy-and-Hold Support


**Goal**: Remove `fee_per_share` from Backtest (keep it in TiConfig only) and add a `Signal.Once()` algo to enable buy-and-hold strategies.
**Architecture**: Two independent changes: (1) API simplification, (2) new signal algo + example
**Tech Stack**: Python, tiportfolio
**Spec**: Extends Chunk 1 implementation

## File Map:

1. Modify : `src/tiportfolio/backtest.py` - Remove `fee_per_share` parameter from Backtest.__init__
2. Modify : `tests/test_backtest.py` - Remove fee_override test, update any tests using fee_per_share in Backtest
3. Modify : `examples/02_custom_config.py` - Use TiConfig(fee_per_share=...) instead of Backtest(fee_per_share=...)
4. Modify : `docs/api/index.md` - Remove fee_per_share from Backtest signature
5. Modify : `docs/superpowers/specs/2026-03-28-core-engine-implementation-design.md` - Remove fee_per_share from Backtest constructor
6. Modify : `src/tiportfolio/algos/signal.py` - Add Signal.Once() algo
7. Modify : `tests/test_signal.py` - Add tests for Signal.Once
8. Create : `examples/06_buy_and_hold.py` - Buy-and-hold QQQ/BIL/GLD example using Signal.Once

## Chunks

### Chunk 1: Remove fee_per_share from Backtest
Files: backtest.py, test_backtest.py, 02_custom_config.py, api/index.md, spec
Steps:
- Step 1: Remove fee_per_share parameter from Backtest.__init__
- Step 2: Update tests
- Step 3: Update example and docs

### Chunk 2: Add Signal.Once + buy-and-hold example
Files: signal.py, test_signal.py, 06_buy_and_hold.py
Steps:
- Step 1: Write test for Signal.Once (fires once, then False forever)
- Step 2: Implement Signal.Once
- Step 3: Write buy-and-hold example
