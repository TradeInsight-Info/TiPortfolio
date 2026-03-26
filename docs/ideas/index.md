
## Goal




## Old and New Terms:
In current TiPortfolio, we uses strategy term a lot, this is so easy to confusing people. For example, we have rebalance strategy and allocation strategy. In bt, it all named as Algo to build Algo Stack. And the algothim combination together to be ready to be backtested in next step, it is named as Strategy, we want to adopy the naming of bt. 

Allocation Stragey -> Algo )




### TIPortfolio

We want to a simpler to use TiPortfolio library to be flexible to backtest differnet asset allocation strategies, the goal is to provide a flexbile python library a cli too for users to use. In the future, we will built AGENT AI skills around the CLI to make is easier to run in AGENT Coding tools such as Claude Code, OpenCode, Gemini CLI, Cursor etc.






### bt proejct as reference

**bt** is a flexible backtesting framework for Python used to test and evaluate trading strategies. We want to borrow some ideas from it. 

Some very positive things about bt:


```
# create the strategy
s = bt.Strategy('s1', [bt.algos.RunMonthly(),
                       bt.algos.SelectAll(),
                       bt.algos.WeighEqually(),
                       bt.algos.Rebalance()])
```

It allows user to create a strategy in just a few lines of code.


```
# create our new strategy
s2 = bt.Strategy('s2', [bt.algos.RunWeekly(),
                        bt.algos.SelectAll(),
                        bt.algos.WeighInvVol(),
                        bt.algos.Rebalance()])

# now let's test it with the same data set. We will also compare it with our first backtest.
test2 = bt.Backtest(s2, data)
# we include test here to see the results side-by-side
res2 = bt.run(test, test2)

res2.plot();
```

You can easily create a new strategy and test it with the same data set, and compare the results side-by-side. This is very useful for us to quickly iterate on our allocation strategy. However, I think the charting plot part we have done better than bt. 


And bt has much more good features and concepts at [bt/docs].




### Core Features of TiPortfolio

1. We want it to be as simple and flexbile as bt.

- User can set up config, fee rate, risk free interest rate, bechmark ticker, and other parameters in a config file or through CLI arguments.
- Set stock tickers, such as QQQ, SPY, GLD
- Create a strategy, or use a built-in one, for example Strategy.MonthlyRebalance
- Create an allocation, or use a built-in one, for example Allocation.EqualWeighting
- Run 
- User will get the backtest result. 
  - An interative chart to show the performance of the strategy vs benchmark, and the allocation of the portfolio over time.
  - A table to show the detailed backtest result, such as the return, volatility, sharpe ratio, sortino ratio, max drawdown, and other metrics. 
  - A pandas dataframe (CSV for cli) to show the trade records, such as the date, ticker, action (buy/sell), quantity, price, and other details.
  - This could be extended by algorithm too, they can add their own column for example for a volatility based strategy, they can add the volatility value at the time of trade, to help them analyze the strategy performance under different market volatility condition.


  2. It supports bt like tree structure. https://pmorissette.github.io/bt/tree.html
  
  - It means, one strategy can be used as in another one, as same level as a ticker


  3. It support bt like algo stacks too. https://pmorissette.github.io/bt/algos.html

  - It support bt like branching logic in algo stack, this will give us real flexbility, for example, I want to have one trigger based on VIX above 25, another one monthly rebalance, if I use OR, it will combine these two into one algo, eitehr happened, it will go to the downstream algos. We should support OR, NOT, (we don't need AND, becasue different algo is AND in an algo stack)


```
import bt

data = bt.get('spy,agg', start='2010-01-01')

# create two separate algo stacks and combine the branches
logging_stack = bt.AlgoStack(
                    bt.algos.RunWeekly(),
                    bt.algos.PrintInfo('{name}:{now}. Value:{_value:0.0f}, Price:{_price:0.4f}')
                    )
trading_stack = bt.AlgoStack(
                    bt.algos.RunMonthly(),
                    bt.algos.SelectAll(),
                    bt.algos.WeighEqually(),
                    bt.algos.Rebalance()
                    )
branch_stack =  bt.AlgoStack(
                    # Upstream algos could go here...
                    bt.algos.Or( [ logging_stack, trading_stack ] )
                    # Downstream algos could go here...
                    )
```





### TiPortfolio Current Pro and Cons


- TiPortfolio interactive chart is better than bt statics one, however, for running in cli mode, static chart is better, interactive chart is better for jupyter notebook. We can support both of them.

- TiPortfolio has no Algo Stack concept, it has two concept, one is AllocationStrategy which is returning the calculated portfolio assets weights, the other one is RebalanceStrategy which is returning the rebalance signal/trigger. We can adop algo stack concept, that user can choose built their own algo stacks. For examaple, a trigger algorithm should be before a rebalance calculating portfolio asset weights algotihm. Adopt this concept to make it simpler and more flexible for users to build their own strategy.


#### Other features

- Debug, it is hard to debug at current stage of tiportfolio, however, we can add one option when DEBUG is enabled in the trading records table it will show much more information, an extra COLUMN, to explain why this trade is made, for example, for a monthly equalt weight strategy, it will say, Rebance because at satrt of month, Sell because current weight is 40%, higher than target 25% percent.


- Additional data, currently at TiPortfolio it received additional data, but in a very inconsistent way, we can make it more consistent, 1 require additional data has same time step as price data, if not alert user, which says users have to prepare the additiona data well before use. For example for trading QQQ and BIL, we can use VIX as additional data to indicate market volatility.






##### Data Fetching

- `@tiportfolio/helpers` We support fetch from alpaca.py and yfinance, there is a problem becasue alpaca.py and yfinacne use different timestamp for data column. Built a layer to normalise it to follow YFinnace. to use UTC timezone, if no timezone info, assume it is in UTC. It is it other timezone, convert it to UTC. This will make it more consistent and easier for users to use the data. The good part is we support caching, which we should continue do so, but add an extra layer to make sure the data is consistent acroos yfinance and alpaca. 



## Structure


Under src/tiportfolio, we can have the following structure:

- core/

Core class and objects
- TiConfig: to define the config schema, and also the default config values, for example, the default fee rate, risk free interest rate, benchmark ticker etc. User can override these values through CLI arguments or config file. This will make it more flexible for users to use the library.
- Algo, for both trigger algo, and rebalance weight algo
- Strategy to receieve, data, algo stacks and run the backtest, backtest will return a backtest result object defined in metrics.py which includes trading records
- Backtest, receive config, algo stacks and run the backtest, return the backtest result containing the trading records
- Metrics, receive backtest result and plotting chart, comparing different backtest results, performance metrics calculation, such as return, volatility, sharpe ratio, sortino ratio, max drawdown, and other metrics.



- utils/
- helpers/ (keep it as it is, to fetch data, this is borrowed from pybroker, but we need to add the data normalisation layer to make sure the data is consistent across different data sources, for example, alpaca and yfinance)







## Metrics

### Charting

- Add plot_histogram()
- plot_security_weights()

### Results



### Testing

Under tests/, we will focus on testing

1. 
