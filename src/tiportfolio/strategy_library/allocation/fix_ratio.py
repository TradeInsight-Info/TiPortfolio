from typing import List

from pandas import Timestamp

from tiportfolio.portfolio.allocation.allocation import PortfolioConfig
from tiportfolio.portfolio.allocation.frequency_based_allocation import (
    FrequencyBasedAllocation,
    RebalanceFrequency,
)
from tiportfolio.portfolio.trading import Trading


class FixRatioFrequencyBasedAllocation(FrequencyBasedAllocation):

    def get_target_ratio(self, current_step: Timestamp, strategy_name: str) -> float:
        # return the fixed value for the strategy
        return self.strategy_ratio_map.get((current_step, strategy_name), 0.0)

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
        if not abs(sum(allocation_ratio_list) - 1.0) < 1e-6:
            raise ValueError("Sum of allocation_percentages must be 1.0")
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
