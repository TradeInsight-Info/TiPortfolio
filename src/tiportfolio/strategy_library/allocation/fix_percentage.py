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

        if self.is_first_step(current_step):
            # On the first step, we set initial allocations directly
            for i in range(len(self.strategies)):
                strategy = self.strategies[i]
                target_allocation = self.allocation_percentages[i]

                idx = (current_step, strategy.unique_name)

                value = self.config.get('initial_capital') * target_allocation
                cost = float(strategy.prices_df.loc[current_step, 'close'])
                quantity = value / cost
                fees = value * self.config.get('fees_config', {}).get('commission', 0.0001)
                cost_basis = value + fees

                self.portfolio_df.loc[idx, 'value'] = value
                self.portfolio_df.loc[idx, 'quantity'] = quantity
                self.portfolio_df.loc[idx, 'fees'] = fees
                self.portfolio_df.loc[idx, 'cost_basis'] = cost_basis

        else:
            for i in range(len(self.strategies)):
                strategy = self.strategies[i]
                target_allocation = self.allocation_percentages[i]

                idx = (current_step, strategy.unique_name)

                previous_step = get_previous_market_open_day(current_step)

                # get previous snapshot
                previous_snapshot = self.get_portfolio_snapshot(previous_step)
                total_portfolio_value = self.get_total_portfolio_value(previous_step)
                new_target_value = total_portfolio_value * target_allocation

                value_diff = new_target_value - previous_snapshot.loc[strategy.unique_name, 'value']

                if abs(value_diff) < 1e-6 or value_diff == 0:
                    continue  # No change needed

                elif value_diff > 0:
                    # Need to buy more
                    cost = float(strategy.prices_df.loc[current_step, 'close'])
                    quantity_to_buy = value_diff / cost
                    fees = value_diff * self.config.get('fees_config', {}).get('commission', 0.0001)

                    new_quantity = previous_snapshot.loc[strategy.unique_name, 'quantity'] + quantity_to_buy
                    new_value = previous_snapshot.loc[strategy.unique_name, 'value'] + value_diff
                    new_cost_basis = previous_snapshot.loc[strategy.unique_name, 'cost_basis'] + value_diff + fees
                else:
                    # Need to sell
                    cost = float(strategy.prices_df.loc[current_step, 'close'])
                    quantity_to_sell = -value_diff / cost
                    fees = -value_diff * self.config.get('fees_config', {}).get('commission', 0.0001)

                    new_quantity = previous_snapshot.loc[strategy.unique_name, 'quantity'] - quantity_to_sell
                    new_value = previous_snapshot.loc[strategy.unique_name, 'value'] + value_diff
                    new_cost_basis = previous_snapshot.loc[strategy.unique_name, 'cost_basis'] + value_diff + fees

                self.portfolio_df.loc[idx, 'value'] = new_value
                self.portfolio_df.loc[idx, 'quantity'] = new_quantity
                self.portfolio_df.loc[idx, 'fees'] = fees
                self.portfolio_df.loc[idx, 'cost_basis'] = new_cost_basis
