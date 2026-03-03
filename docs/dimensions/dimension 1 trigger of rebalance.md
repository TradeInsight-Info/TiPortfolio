Dimension 1: When to Rebalance


- Fix time Scheduled Rebalance, for example, every quarter, every year, every start of month, end of month, middle of month, every Monday, every Wednesaday, every Friday

  - todo under sheduled rebalance, we should have one strategy is no rebalance, with a special rebalance frequecy is `never`.

- Market Volatility Rebalance, for example, at VIX about 30, reduce high volatility assets, like in a QQQ, BIL portfolio, if VIX is high, QQQ percetange should og low, BIL should go up, vice versa. 
  - And if we pass a freezing time as a parameter (default is 0), like 7 days, if last rebalance is less than 7 days ago, then no rebalance.
  - ~~Combination of Fix Time Schedule + Trigger Event, for example, we only rebalance at middle month, and if VIX is 10 plus or minus then last month, or VIX is 20% higher or lower comparting to last rebalance, or comparing to a base line~~ (This is the original idea, but a freezing time makes more sense)




