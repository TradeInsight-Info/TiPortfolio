# TiPortfolio
A portfolio management tool with built-in state-of-the-art portfolio optimization algorithms, with extensibility for different use cases for both institutes and retail traders.


This project is built and tested with Python 3.12, however, it should be compatible with Python 3.10 and above.

## Features
> including features work in progress


- [ ] Dollar neutral
- [ ] Beta neutral
- [ ] Tail risk management
- [ ] Volatility Targeting
- [ ] Drawdown control
- [ ] Simple Backtesting






```mermaid
mindmap
root((TiPortfolio))
	Methodologies
		Dollar Neutral
		Beta Neutral
		Volatility Targeting
		Tail Risk Management
		Drawdown Control
	Concepts
		Volatility
		Kelly Formula
```


```mermaid

graph TD

    A[Portfolio Risk Management]

    A --> B[Dollar Neutral]
    A --> C[Beta Neutral]
    A --> D[Volatility Targeting]
    A --> E[Drawdown Control]
    A --> F[Tail Risk Management]

    C --reduces--> E
    D --stabilizes--> E
    F --protects against--> E

    D --not subset of--> F
    E --not same as--> F
    B --independent of--> C

```



