from typing import List

from pandas import Timestamp

from tiportfolio.portfolio.allocation.allocation import (
    CASH_STRATEGY_NAME,
    PortfolioConfig,
)
from tiportfolio.portfolio.allocation.frequency_based_allocation import (
    FrequencyBasedAllocation,
    RebalanceFrequency,
)
from tiportfolio.portfolio.trading import Trading


class FixRatioFrequencyBasedAllocation(FrequencyBasedAllocation):

    def get_target_ratio(self, current_step: Timestamp, strategy_name: str) -> float:
        # Handle cash strategy - calculate automatically
        if strategy_name == CASH_STRATEGY_NAME:
            # Cash ratio = 1.0 - sum of all stock strategy ratios
            total_stock_ratio = sum(self.allocation_percentages)
            return 1.0 - total_stock_ratio
        
        # return the fixed value for the strategy from allocation_percentages
        for i, strategy in enumerate(self.strategies):
            if strategy.name == strategy_name:
                return self.allocation_percentages[i]
        # Strategy not found (should not happen in normal operation)
        raise ValueError(f"Strategy '{strategy_name}' not found in strategies list")

    def __init__(
            self,
            config: PortfolioConfig,
            strategies: List[Trading],
            allocation_ratio_list: List[float],
            rebalance_frequency: RebalanceFrequency,
            market_name: str = 'NYSE',
            hour: int = 9,
            minute: int = 30,
    ) -> None:

        if len(allocation_ratio_list) != len(strategies):
            raise ValueError(
                "Length of allocation_percentages must match number of strategy_library"
            )
        # Allow sum to be <= 1.0 (remaining goes to cash)
        if sum(allocation_ratio_list) > 1.0:
            raise ValueError("Sum of allocation_percentages must be <= 1.0")
        self.allocation_percentages = allocation_ratio_list
        self.rebalance_frequency = rebalance_frequency
        super().__init__(
            config, strategies, rebalance_frequency, market_name, hour, minute
        )

    def is_time_to_rebalance(self, current_step: Timestamp) -> bool:
        return super().is_time_to_rebalance(current_step)

    def rebalance(self, current_step: Timestamp) -> None:
        for i in range(len(self.strategies)):
            self.strategy_ratio_map[(current_step, str(self.strategies[i]))] = self.allocation_percentages[i]
