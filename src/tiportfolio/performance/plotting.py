from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from pandas import Timestamp


def plot_portfolio_value(
    steps: List[Timestamp],
    portfolio_values: List[float],
    strategy_values_dict: Dict[str, List[float]],
    rebalance_dates: Optional[List[Timestamp]] = None,
    initial_capital: Optional[float] = None,
    figsize: Tuple[float, float] = (12, 6),
    show_strategies: bool = True,
    show_rebalance_dates: bool = True,
) -> None:
    """
    Plot portfolio value over time with strategy breakdown and rebalance dates.

    Args:
        steps: List of datetime steps for x-axis.
        portfolio_values: Total portfolio value at each step.
        strategy_values_dict: Dictionary mapping strategy names to their values
            at each step. Keys are strategy names, values are lists of floats
            corresponding to each step.
        rebalance_dates: Optional list of rebalance dates to mark on the plot.
        initial_capital: Optional initial capital value to display as a
            horizontal reference line.
        figsize: Figure size (width, height) in inches.
        show_strategies: Whether to show individual strategy values.
        show_rebalance_dates: Whether to mark rebalance dates.

    Raises:
        ValueError: If inputs are invalid or insufficient data.
    """
    if len(steps) != len(portfolio_values):
        raise ValueError(
            "steps and portfolio_values must have the same length."
        )

    if len(steps) < 1:
        raise ValueError(
            "Insufficient data to plot. Need at least 1 time step."
        )

    if show_strategies:
        for strategy_name, values in strategy_values_dict.items():
            if len(values) != len(steps):
                raise ValueError(
                    f"Strategy '{strategy_name}' values length "
                    f"({len(values)}) must match steps length ({len(steps)})."
                )

    # Create figure and axes
    _, ax = plt.subplots(figsize=figsize)

    # Plot initial capital reference line if provided
    if initial_capital is not None:
        ax.axhline(
            y=initial_capital,
            color="gray",
            linestyle="-.",
            alpha=0.5,
            linewidth=1.5,
            label="Initial Capital",
            zorder=1,
        )

    # Plot total portfolio value
    ax.plot(
        steps,
        portfolio_values,
        label="Total Portfolio",
        linewidth=2,
        color="black",
        zorder=3,
    )

    # Plot individual strategy values if requested
    if show_strategies and strategy_values_dict:
        strategy_names = sorted(strategy_values_dict.keys())
        colormap = cm.get_cmap("tab10")
        colors = [colormap(i) for i in range(len(strategy_names))]

        for i, strategy_name in enumerate(strategy_names):
            strategy_values = strategy_values_dict[strategy_name]
            ax.plot(
                steps,
                strategy_values,
                label=f"Strategy: {strategy_name}",
                linewidth=1.5,
                color=colors[i],
                alpha=0.7,
                linestyle="--",
                zorder=2,
            )

    # Mark rebalance dates if requested
    if show_rebalance_dates and rebalance_dates:
        steps_set = set(steps)
        for i, rebalance_date in enumerate(rebalance_dates):
            if rebalance_date in steps_set:
                ax.axvline(
                    x=rebalance_date,  # type: ignore[arg-type]
                    color="red",
                    linestyle=":",
                    alpha=0.6,
                    linewidth=1,
                    label="Rebalance" if i == 0 else "",
                    zorder=2,
                )

    # Formatting
    ax.set_xlabel("Step (Datetime)", fontsize=11)
    ax.set_ylabel("Portfolio Value", fontsize=11)
    ax.set_title("Portfolio Value Over Time", fontsize=13, fontweight="bold")
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
