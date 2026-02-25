from typing import List, Tuple, Optional, Dict
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
    
    Risky assets are scaled by Target_Vol / Current_VIX.
    Remaining weight is distributed equally among safe assets.
    """

    def __init__(
        self,
        config: PortfolioConfig,
        strategies: List[Trading],
        vix_data: pd.Series,
        base_weights: Dict[str, float],
        risky_assets: List[str],
        target_vol: float = 15.0,
        vix_boundaries: Tuple[float, float] = (-0.5, 6.0),
        max_leverage: float = 1.0,
    ) -> None:
        """
        Initialize VixTargetingAllocation.

        Args:
            config: Portfolio configuration.
            strategies: List of strategies to allocate to.
            vix_data: Pandas Series of VIX values, indexed by datetime.
            base_weights: Base weights for each strategy (e.g., {"VOO": 0.9, "BIL": 0.1}).
            risky_assets: List of strategy names that are considered risky and will be scaled.
            target_vol: Target annualized volatility for the portfolio.
            vix_boundaries: (low_offset, high_offset) Relative to target_vol, triggers a rebalance when crossed.
            max_leverage: Maximum total weight for all strategies.
        """
        super().__init__(config, strategies)
        self.vix_data = vix_data.sort_index()
        self.base_weights = base_weights
        self.risky_assets = risky_assets
        self.target_vol = target_vol
        self.vix_boundaries = vix_boundaries
        self.max_leverage = max_leverage
        
        # Internal cache for weights at each step
        self._current_weights: dict[str, float] = {}
        # Keep track of last rebalance VIX to avoid repeated logs
        self._last_vix: float = -1.0
        
        # Internal cache for regime edge-triggering and performance
        self._current_regime: Optional[str] = None
        self._last_checked_step: Optional[Timestamp] = None
        self._last_rebalance_result: bool = False
        self._last_rebalance_step: Optional[Timestamp] = None

    def is_time_to_rebalance(self, current_step: Timestamp) -> bool:
        """
        Determine if it's time to rebalance based on VIX levels crossing thresholds.
        """
        if getattr(self, "_last_checked_step", None) == current_step:
            return getattr(self, "_last_rebalance_result", False)
            
        self._last_checked_step = current_step
        
        vix = self.vix_data.asof(current_step)
        if pd.isna(vix):
            self._last_rebalance_result = False
            return False
            
        low = self.target_vol + self.vix_boundaries[0]
        high = self.target_vol + self.vix_boundaries[1]
        
        if vix < low:
            new_regime = "low"
        elif vix > high:
            new_regime = "high"
        else:
            new_regime = "normal"

        if self.is_first_step(current_step):
            self._current_regime = new_regime
            self._last_rebalance_result = True
            return True
            
        if new_regime != self._current_regime:
            self._current_regime = new_regime
            self._last_rebalance_result = True
            return True
            
        self._last_rebalance_result = False
        return False

    def get_target_ratio(self, current_step: Timestamp, strategy_name: str) -> float:
        """
        Calculate target allocation ratio based on current VIX level.
        """
        # 1. On rebalance steps, calculate new weights EXACTLY ONCE
        if self.is_time_to_rebalance(current_step):
            if current_step != getattr(self, "_last_rebalance_step", None):
                vix = self.vix_data.asof(current_step)
                
                if pd.isna(vix) or vix <= 0:
                    logger.warning(
                        "Invalid VIX value at %s: %s. Keeping previous weights.",
                        current_step, vix
                    )
                else:
                    new_weights = {}
                    multiplier = self.target_vol / vix
                    
                    total_risky_weight = 0.0
                    for strat_name in self.risky_assets:
                        base_weight = self.base_weights.get(strat_name, 0.0)
                        w = base_weight * multiplier
                        new_weights[strat_name] = w
                        total_risky_weight += w
                        
                    # Cap total risky weight
                    if total_risky_weight > self.max_leverage:
                        scale = self.max_leverage / total_risky_weight
                        for strat_name in self.risky_assets:
                            new_weights[strat_name] *= scale
                        total_risky_weight = self.max_leverage
                        
                    # Distribute remaining weight to safe assets
                    remaining_weight = self.max_leverage - total_risky_weight
                    safe_assets = [s.name for s in self.strategies if s.name not in self.risky_assets]
                    
                    if safe_assets:
                        weight_per_safe_asset = remaining_weight / len(safe_assets)
                        for strat_name in safe_assets:
                            new_weights[strat_name] = weight_per_safe_asset
                    
                    # Ensure all strategies are in the new_weights dict
                    for strategy in self.strategies:
                        if strategy.name not in new_weights:
                            new_weights[strategy.name] = 0.0
                            
                    if CASH_STRATEGY_NAME not in new_weights:
                        new_weights[CASH_STRATEGY_NAME] = 1.0 - sum(new_weights.get(s.name, 0.0) for s in self.strategies)
                    
                    self._current_weights = new_weights
                    self._last_vix = vix
                    self._last_rebalance_step = current_step

        # 2. Return cached weight for the requested strategy
        if strategy_name in self._current_weights:
            return self._current_weights[strategy_name]
            
        # If no weights cached yet (shouldn't happen if rebalance triggers correctly)
        if strategy_name == CASH_STRATEGY_NAME:
            return 1.0
        return 0.0
