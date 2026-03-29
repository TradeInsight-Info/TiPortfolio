"""
02 — Custom Config: Impact of Fees on Returns
==============================================

Run the same strategy twice with different fee structures to see
how transaction costs eat into returns over time.

Key concept: TiConfig lets you override simulation parameters.
The `fee_per_share` parameter models brokerage commissions.
"""

import tiportfolio as ti

data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31")
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

# Run all three
result_low = ti.run(bt_low)
result_high = ti.run(bt_high)
result_big = ti.run(bt_big)

print("=== Low Fee (default $0.0035/share) ===")
print(result_low.summary())
print()

print("=== High Fee ($0.05/share) ===")
print(result_high.summary())
print()

print("=== Large Capital ($100k, default fees) ===")
print(result_big.summary())
print()

# Note: with equal-weight monthly rebalance, higher fees reduce returns
# but the difference is small for low-turnover strategies like this.
