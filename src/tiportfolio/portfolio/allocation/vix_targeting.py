from typing import List, Tuple
import pandas as pd
from pandas import Timestamp

from tiportfolio.portfolio.allocation.allocation import (
    Allocation,
    CASH_STRATEGY_NAME,
    PortfolioConfig,
)
from tiportfolio.portfolio.trading import Trading
from tiportfolio.utils.default_logger import logger


class VixTargetingAllocation(Allocation):
    """
    Allocation strategy that targets a specific portfolio volatility level 
    using the VIX index as a market volatility proxy.
    
    Rebalancing is triggered only when the VIX index moves outside a 
    specified target range.
    
    Weights are calculated such that each strategy contributes equally 
    to the target portfolio volatility:
    W_i = Target_Vol / (N * VIX * Volatility_Flag_i)
    
    The total weight is capped by max_leverage. The remainder is cash.
    """

    def __init__(
        self,
        config: PortfolioConfig,
        strategies: List[Trading],
        vix_data: pd.Series,
        volatility_flags: List[float],
        target_vol: float = 15.0,
        target_range: Tuple[float, float] = (15.0, 30.0),
        max_leverage: float = 1.0,
    ) -> None:
        """
        Initialize VixTargetingAllocation.

        Args:
            config: Portfolio configuration.
            strategies: List of strategies to allocate to.
            vix_data: Pandas Series of VIX values, indexed by datetime.
            volatility_flags: Sensitivity of each strategy to market volatility.
            target_vol: Target annualized volatility for the portfolio.
            target_range: (low, high) VIX levels that trigger a rebalance.
            max_leverage: Maximum total weight for all strategies.
        """
        if len(volatility_flags) != len(strategies):
            raise ValueError(
                "Length of volatility_flags must match number of strategies"
            )
            
        super().__init__(config, strategies)
        self.vix_data = vix_data.sort_index()
        self.volatility_flags = volatility_flags
        self.target_vol = target_vol
        self.target_range = target_range
        self.max_leverage = max_leverage
        
        # Internal cache for weights at each step
        self._current_weights: dict[str, float] = {}
        # Keep track of last rebalance VIX to avoid repeated logs
        self._last_vix: float = -1.0

    def is_time_to_rebalance(self, current_step: Timestamp) -> bool:
        """
        Determine if it's time to rebalance based on VIX levels.
        """
        # Always rebalance on the first step to set initial positions
        if self.is_first_step(current_step):
            return True
            
        vix = self.vix_data.asof(current_step)
        if pd.isna(vix):
            return False
            
        low, high = self.target_range
        if vix < low or vix > high:
            return True
            
        return False

    def get_target_ratio(self, current_step: Timestamp, strategy_name: str) -> float:
        """
        Calculate target allocation ratio based on current VIX level.
        """
        # 1. On rebalance steps, calculate new weights
        if self.is_time_to_rebalance(current_step):
            vix = self.vix_data.asof(current_step)
            
            if pd.isna(vix) or vix <= 0:
                logger.warning(
                    "Invalid VIX value at %s: %s. Keeping previous weights.",
                    current_step, vix
                )
            else:
                # Formula: W_i = Target_Vol / (N * VIX * Flag_i)
                num_strategies = len(self.strategies)
                weights = []
                for flag in self.volatility_flags:
                    w = self.target_vol / (num_strategies * vix * flag)
                    weights.append(w)
                
                # Cap total risky weight by max_leverage
                total_risky = sum(weights)
                if total_risky > self.max_leverage:
                    scale = self.max_leverage / total_risky
                    weights = [w * scale for w in weights]
                
                # Update current weights cache
                new_weights = {}
                for i, strategy in enumerate(self.strategies):
                    new_weights[strategy.name] = weights[i]
                
                total_risky_capped = sum(weights)
                new_weights[CASH_STRATEGY_NAME] = 1.0 - total_risky_capped
                
                self._current_weights = new_weights
                self._last_vix = vix

        # 2. Return cached weight for the requested strategy
        if strategy_name in self._current_weights:
            return self._current_weights[strategy_name]
            
        # If no weights cached yet (shouldn't happen if rebalance triggers correctly)
        if strategy_name == CASH_STRATEGY_NAME:
            return 1.0
        return 0.0
