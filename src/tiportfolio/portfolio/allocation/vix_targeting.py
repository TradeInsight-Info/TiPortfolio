from typing import List
import pandas as pd
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
from tiportfolio.utils.default_logger import logger


class VixTargetingAllocation(FrequencyBasedAllocation):
    """
    Allocation strategy that targets a specific volatility level based on the
    VIX index.

    The weight of risky assets is calculated as:
    weight = target_vol / VIX_value

    This weight is then capped by max_leverage.
    The remaining allocation goes to cash.
    """

    def __init__(
        self,
        config: PortfolioConfig,
        strategies: List[Trading],
        vix_data: pd.Series,
        target_vol: float = 15.0,
        max_leverage: float = 1.0,
        rebalance_frequency: RebalanceFrequency = RebalanceFrequency.daily,
        hour: int = 9,
        minute: int = 30,
    ) -> None:
        """
        Initialize VixTargetingAllocation.

        Args:
            config: Portfolio configuration.
            strategies: List of risky strategies to allocate to.
            vix_data: Pandas Series of VIX values, indexed by datetime.
            target_vol: Target annualized volatility (e.g., 15.0 for 15%).
            max_leverage: Maximum total weight for all risky strategies.
            rebalance_frequency: How often to rebalance.
            hour: Rebalance hour.
            minute: Rebalance minute.
        """
        super().__init__(config, strategies, rebalance_frequency, hour, minute)
        self.vix_data = vix_data.sort_index()
        self.target_vol = target_vol
        self.max_leverage = max_leverage

        # Internal cache for weights at each rebalance step
        self._step_weights: dict[Timestamp, float] = {}

    def get_target_ratio(self, current_step: Timestamp, strategy_name: str) -> float:
        """
        Calculate target allocation ratio for a strategy at a given time step.
        """
        # 1. Calculate the total risky weight for this step if not already cached
        if current_step not in self._step_weights:
            # Find the most recent VIX value at or before current_step
            # We use asof to get the latest available VIX data
            vix_value = self.vix_data.asof(current_step)

            if pd.isna(vix_value) or vix_value <= 0:
                logger.warning(
                    "Invalid VIX value at %s: %s. Using default weight 0.0.",
                    current_step, vix_value
                )
                total_risky_weight = 0.0
            else:
                # Formula: target_vol / VIX
                total_risky_weight = self.target_vol / vix_value
                total_risky_weight = min(total_risky_weight, self.max_leverage)

            self._step_weights[current_step] = total_risky_weight

        total_risky_weight = self._step_weights[current_step]

        # 2. Handle cash strategy
        if strategy_name == CASH_STRATEGY_NAME:
            return 1.0 - total_risky_weight

        # 3. Handle risky strategies
        # If multiple risky strategies are provided, split the total_risky_weight
        # equally among them. In most use cases, only one risky strategy
        # is provided.
        num_risky_strategies = len(self.strategies)
        for strategy in self.strategies:
            if strategy.name == strategy_name:
                return total_risky_weight / num_risky_strategies

        raise ValueError(
            f"Strategy '{strategy_name}' not found in VixTargetingAllocation"
        )
