from datetime import datetime, timedelta
from typing import List

from tiportfolio.portfolio.allocation.allocation import Allocation


class FixPercentageAllocation(Allocation):

    def __init__(self, config, strategies, allocation_percentages: List[float], rebalance_frequency: timedelta) -> None:
        super().__init__(config, strategies)
        if len(allocation_percentages) != len(strategies):
            raise ValueError("Length of allocation_percentages must match number of strategies")
        if not abs(sum(allocation_percentages) - 1.0) < 1e-6:
            raise ValueError("Sum of allocation_percentages must be 1.0")
        self.allocation_percentages = allocation_percentages
        self.rebalance_frequency = rebalance_frequency

    def is_time_to_rebalance(self, current_step: datetime) -> bool:

        if (current_step - self.time_index[0]) % self.rebalance_frequency == timedelta(0):
            return True
        return False

    def rebalance(self, current_step: datetime) -> None:
        pass
