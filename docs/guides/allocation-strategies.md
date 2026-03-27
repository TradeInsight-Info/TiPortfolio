

## Built-in Allocation Strategies


### Dollar Neutral

> Through SelectMomentum



```python
import pandas as pd
import tiportfolio as ti

tickers = [
    "MSFT",   # Technology
    "NVDA",   # Technology
    "AMZN",   # Consumer Discretionary
    "JPM",    # Financials
    "LLY",    # Healthcare
    "XOM",    # Energy
    "COST",   # Consumer Staples
    "GOOGL",  # Communications
    "CAT",    # Industrials
    "PLD",    # Real Estate

    "INTC",   # Technology
    "AMD",    # Technology
    "ETSY",   # Consumer Discretionary
    "WFC",    # Financials
    "PFE",    # Healthcare
    "CVX",    # Energy
    "KR",     # Consumer Staples
    "SNAP",   # Communications
    "DE",     # Industrials
    "MPW",    # Real Estate
] # Todo Fetch All Stocks from US Stock Market


data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31") 

lookback = pd.DateOffset(months=1)   
lag = pd.DateOffset(days=1) # 1 day lag to avoid lookahead bias

long = ti.Portfolio(
    'long',
    [
        ti.algo.Select.Momentum(
            n=3,
            lookback=lookback,
            lag=lag,
            sort_descending=True,
        ),
        ti.algo.Weigh.Equally(),
        ti.algo.Action.Rebalance(),
    ],
    tickers,
)

short = ti.Portfolio(
    'short',
    [
        ti.algo.Select.Momentum(
            n=3,
            lookback=lookback,
            lag=lag,
            sort_descending=False,
        ),
        ti.algo.Weigh.Equally(sign=-1),
        ti.algo.Action.Rebalance(),
    ],
    tickers,
)

dollar_neutral_portfolio = ti.Portfolio(
    'dollar_neutral',
    [
        ti.algo.Schedule.Monthly(),
        ti.algo.Select.All(),    # selects child portfolio names: ["long", "short"]
        ti.algo.Weigh.Equally(), # 50% capital to each child
        ti.algo.Action.Rebalance(),    # allocates capital to children
    ],
    [long, short],
)

result = ti.run(ti.Backtest(dollar_neutral_portfolio, data))
```



### Voaltility Targeting

A volatility targeting strategy is a different animal from dollar-neutral or beta-neutral — instead of balancing longs vs. shorts, it dynamically sizes your entire position based on the portfolio's realized volatility, scaling up when markets are calm and scaling down when they get choppy. 


```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]


data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31") 

portfolio = ti.Portfolio(
    'monthly',
    [
        ti.algo.Schedule.Monthly(),
        ti.algo.Select.All(),
        ti.algo.Weigh.BasedOnHV(
            initial_ratio={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1},
            target_hv=60,
            lookback=pd.DateOffset(months=1),
        ),
        ti.algo.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
```


### Equal Risk Contribution (ERC)

ERC — also known as Risk Parity — sizes each asset so that every position contributes the same amount of risk to the total portfolio, rather than equal capital weight. Compared to a minimum-variance portfolio it is more diversified; compared to an equal-weight portfolio it is less volatile. It sits between the two.

Unlike `Weigh.BasedOnHV` (which ignores correlation) or `Weigh.BasedOnBeta` (which targets a single factor), ERC accounts for the full covariance structure of returns, so correlated assets naturally receive smaller allocations.

```python
import pandas as pd
import tiportfolio as ti

tickers = ["SPY", "TLT", "GLD", "BIL"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    'erc_monthly',
    [
        ti.algo.Schedule.Monthly(),
        ti.algo.Select.All(),
        ti.algo.Weigh.ERC(
            lookback=pd.DateOffset(months=3),  # covariance estimation window
            covar_method="ledoit-wolf",         # shrinkage estimator (default)
            risk_parity_method="ccd",           # cyclical coordinate descent (default)
            maximum_iterations=100,
            tolerance=1e-8,
        ),
        ti.algo.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
result.plot()
result.plot_security_weights()  # shows how weights shift as correlations change
```

The weights update every month as the covariance matrix is re-estimated. During equity sell-offs, SPY and TLT often decorrelate, so TLT's weight rises automatically — no manual regime switch needed.



### Beta Neutral Strategy

If your longs have a high beta, you short more of a low-beta stock to offset it, keeping your net portfolio beta at zero.


```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]


data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31") 

portfolio = ti.Portfolio(
    'monthly',
    [
        ti.algo.Schedule.Monthly(),
        ti.algo.Select.All(),
        ti.algo.Weigh.BasedOnBeta(
            initial_ratio={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1},
            target_beta=0,
            lookback=pd.DateOffset(months=1),
        ),
        ti.algo.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
```