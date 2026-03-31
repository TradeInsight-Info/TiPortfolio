"""
05 — Debug with PrintInfo
==========================

Action.PrintInfo prints the algo state on every rebalance date:
date, portfolio name, selected tickers, and weights.

Place it BEFORE Action.Rebalance in the algo stack to see what
the engine will trade. Place it AFTER to confirm what happened.

This is invaluable for debugging why a strategy behaves unexpectedly.
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

data = ti.fetch_data(["QQQ", "BIL"], start="2024-01-01", end="2024-06-30", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "debug_demo",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.PrintInfo(),   # <-- prints state before rebalance
        ti.Action.Rebalance(),
    ],
    ["QQQ", "BIL"],
)

print("=== Running with PrintInfo — watch the algo trace ===")
print()
result = ti.run(ti.Backtest(portfolio, data))
print()
print("=== Summary ===")
print(result.summary())

# You should see output like:
# [2024-01-31] portfolio=debug_demo selected=['QQQ', 'BIL'] weights={'QQQ': 0.5, 'BIL': 0.5}
# [2024-02-29] portfolio=debug_demo selected=['QQQ', 'BIL'] weights={'QQQ': 0.5, 'BIL': 0.5}
# ...
