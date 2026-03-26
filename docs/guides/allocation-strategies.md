

## Built-in Allocation Strategies


### Dollar Neutral

> Through SelectMomentum



```python
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
        ti.algos.SelectMomentum(
            n=3, 
            lookback=lookback,
            lag=lag,
            sort_descending=True
        ), # select top 3 momentum stocks based on last month prices, with 1 bar lag bydefault 
        ti.algo.WeighEqualy(),
        ti.algo.Rebalance() # Action
    ],
    tickers
)

short = ti.Portfolio(
    'short',
    [
        ti.algos.SelectMomentum(
            n=3, 
            lookback=lookback,                                               sort_descending=False
        ), # select bottom 3 momentum stocks based on last month prices
        ti.algo.WeighEqualy(-1),
        ti.algo.Rebalance() # Action
    ]
)

dollar_neutral_portfolio = ti.Portfolio(
    'dollar_neutral',
    [
        bt.algo.ScheduleMonthly(),
        bt.algo.SelectAll(),
        bt.algo.WeighEqually(),
    ],
    [long, short]
)

test = ti.Backtest(dollar_neutral_portfolio, data)
result = ti.run_backtest(test)
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
        ti.algo.ScheduleMonthly(),
        ti.algo.SelectAll(),
        ti.algo.WeighBasedOnHV(initial_ratio={"QQQ":0.7, "BIL":0.2, "GLD":0.1}, target_hv=60, lookback=pd.DateOffset(months=1)),  
        ti.algo.Rebalance()
    ],
    tickers # match tickers
)


test = ti.Backtest(portfolio, data)
result = ti.run_backtest(test)
```


### Beta Neutral Strategy

If your longs have a high beta, you short more of a low-beta stock to offset it, keeping your net portfolio beta at zero.


```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]


data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31") 

portfolio = ti.Portfolio(
    'monthly',
    [
        ti.algo.ScheduleMonthly(),
        ti.algo.SelectAll(),
        ti.algo.WeighBasedOnBeta(initial_ratio={"QQQ":0.7, "BIL":0.2, "GLD":0.1}, target_beta=0, lookback=pd.DateOffset(months=1)),  
        ti.algo.Rebalance()
    ],
    tickers # match tickers
)


test = ti.Backtest(portfolio, data)
result = ti.run_backtest(test)
```