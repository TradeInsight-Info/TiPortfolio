"""
02 — Custom Config: Impact of Fees on Returns
==============================================

Run the same strategy with different fee structures and compare
side by side using ti.run(bt1, bt2, bt3).

Key concept: TiConfig lets you override simulation parameters.
The `fee_per_share` parameter models brokerage commissions.
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31", csv=CSV_DATA)
tickers = ["QQQ", "BIL", "GLD"]
algos = [
    ti.Signal.Monthly(),
    ti.Select.All(),
    ti.Weigh.Equally(),
    ti.Action.Rebalance(),
]

# --- Backtest 1: Default fees ($0.0035/share) ---
portfolio_low = ti.Portfolio("low_fee", list(algos), tickers)
bt_low = ti.Backtest(portfolio_low, data)

# --- Backtest 2: High fees ($0.05/share — simulating an expensive broker) ---
portfolio_high = ti.Portfolio("high_fee", list(algos), tickers)
config_high = ti.TiConfig(fee_per_share=0.05)
bt_high = ti.Backtest(portfolio_high, data, config=config_high)

# --- Backtest 3: Large starting capital ($100k instead of $10k) ---
portfolio_big = ti.Portfolio("big_capital", list(algos), tickers)
config_big = ti.TiConfig(initial_capital=100_000)
bt_big = ti.Backtest(portfolio_big, data, config=config_big)

# Run all three in one call — result is a side-by-side comparison
result = ti.run(bt_low, bt_high, bt_big)

print("=== Side-by-Side Comparison ===")
print(result.summary())
print()

# Note: with equal-weight monthly rebalance, higher fees reduce returns
# but the difference is small for low-turnover strategies like this.
