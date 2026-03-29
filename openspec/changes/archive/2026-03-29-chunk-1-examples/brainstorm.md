# Chunk 1 Examples


**Goal**: Create runnable example scripts demonstrating every capability available in Chunk 1.
**Architecture**: Each example is a standalone `.py` file in `examples/` — users can run any file independently.
**Tech Stack**: Python, tiportfolio (Chunk 1 API only)
**Spec**: Scoped to Chunk 1: Signal.Monthly, Select.All, Weigh.Equally, Action.Rebalance, summary(), plot()

## File Map:

1. Create : `examples/01_quick_start.py` - The Quick Example from api/index.md — monthly equal-weight rebalance of 3 ETFs
2. Create : `examples/02_custom_config.py` - Customise fees, initial capital, and compare summary output
3. Create : `examples/03_two_asset_bond_equity.py` - Classic 60/40-style equal-weight bond + equity split
4. Create : `examples/04_single_asset.py` - Single-ticker buy-and-hold via monthly equal-weight with 1 ticker
5. Create : `examples/05_debug_with_printinfo.py` - Using Action.PrintInfo to trace algo execution

## Chunks

### Chunk 1: Example files
Each file is independent. All use `ti.fetch_data` with real tickers (for live runs) but can also be adapted to fixture data.

Files:
- `examples/01_quick_start.py` through `examples/05_debug_with_printinfo.py`

Steps:
- Step 1: Create examples directory
- Step 2: Write each example file
- Step 3: Verify each example runs with `uv run python examples/01_quick_start.py`
