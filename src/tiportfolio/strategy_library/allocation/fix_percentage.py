from typing import List

from pandas import Timestamp

from tiportfolio.portfolio.allocation.allocation import PortfolioConfig
from tiportfolio.portfolio.allocation.frequency_based_allocation import (
    FrequencyBasedAllocation,
    RebalanceFrequency,
)
from tiportfolio.portfolio.trading_algorithm import TradingAlgorithm
from tiportfolio.utils.get_previous_market_datetime import get_previous_market_open_day


class FixPercentageFrequencyBasedAllocation(FrequencyBasedAllocation):

    def __init__(
            self,
            config: PortfolioConfig,
            strategies: List[TradingAlgorithm],
            allocation_percentages: List[float],
            rebalance_frequency: RebalanceFrequency,
            market_name: str = 'NYSE',
            hour: int = 9,
            minute: int = 30,
    ) -> None:

        if len(allocation_percentages) != len(strategies):
            raise ValueError(
                "Length of allocation_percentages must match number of strategy_library"
            )
        if not abs(sum(allocation_percentages) - 1.0) < 1e-6:
            raise ValueError("Sum of allocation_percentages must be 1.0")
        self.allocation_percentages = allocation_percentages
        self.rebalance_frequency = rebalance_frequency
        super().__init__(
            config, strategies, rebalance_frequency, market_name, hour, minute
        )

    def is_time_to_rebalance(self, current_step: Timestamp) -> bool:
        return super().is_time_to_rebalance(current_step)

    def rebalance(self, current_step: Timestamp) -> None:
        for i in range(len(self.strategies)):
            strategy = self.strategies[i]
            target_allocation = self.allocation_percentages[i]
            target_value = self.config.get('initial_capital') * target_allocation

            close_price = strategy.prices_df.loc[current_step, 'close']
            target_quantity = target_value / close_price

            self.strategy_quantity_map.setdefault(current_step, {})[strategy.unique_name] = target_quantity
