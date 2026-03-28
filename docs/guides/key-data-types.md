## Key Data Types


### `TiConfig` — Global Defaults

```python
import tiportfolio as ti

config = ti.TiConfig(
    fee_per_share=0.0035,    # commission per share traded
    risk_free_rate=0.04,     # annualised, used for Sharpe/Sortino calculation
    loan_rate=0.0514,        # annualised borrowing cost for leveraged positions
    stock_borrow_rate=0.07,  # short-selling borrow fee; varies by security
    initial_capital=10_000,  # starting portfolio value
    bars_per_year=252,       # trading days per year (adjust for intraday data)
)

result = ti.run(ti.Backtest(portfolio, data, config=config))
```

`bars_per_year` depends on your data frequency:

| Frequency | Value |
|---|---|
| Daily (default) | `252` |
| Hourly | `252 * 6.5 ≈ 1638` |
| Minute | `252 * 6.5 * 60 ≈ 98_280` |
