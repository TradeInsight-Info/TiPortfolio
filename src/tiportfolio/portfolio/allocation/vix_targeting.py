from typing import List, Tuple, Optional
import pandas as pd
from pandas import Timestamp

from tiportfolio.portfolio.allocation.allocation import (
    Allocation,
    CASH_STRATEGY_NAME,
    PortfolioConfig,
)
from tiportfolio.portfolio.trading import Trading
from tiportfolio.utils.default_logger import logger
from tiportfolio.utils.market_data import fetch_beta


class VixTargetingAllocation(Allocation):
    """
    Allocation strategy that targets a specific portfolio volatility level 
    using the VIX index as a market volatility proxy.
    
    Rebalancing is triggered only when the VIX index moves outside a 
    specified target range.
    
    Weights are calculated such that each strategy contributes equally 
    to the target portfolio volatility:
    W_i = Target_Vol / (N * VIX * Risk_Multiplier_i)
    
    The total weight is capped by max_leverage. The remainder is cash.
    """

    def __init__(
        self,
        config: PortfolioConfig,
        strategies: List[Trading],
        vix_data: pd.Series,
        risk_multipliers: Optional[List[float]] = None,
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
            risk_multipliers: Sensitivity of each strategy to market volatility. If None, beta values will be fetched from Yahoo Finance.
            target_vol: Target annualized volatility for the portfolio.
            vix_boundaries: (low_offset, high_offset) Relative to target_vol, triggers a rebalance when crossed.
            max_leverage: Maximum total weight for all strategies.
        """
        if risk_multipliers is None:
            logger.info("risk_multipliers not provided. Auto-fetching Beta values from Yahoo Finance...")
            risk_multipliers = []
            for strategy in strategies:
                try:
                    beta = fetch_beta(getattr(strategy, 'symbol_stock', ''))
                    risk_multipliers.append(beta)
                except Exception as e:
                    raise ValueError(f"Failed to auto-fetch beta for strategy '{strategy.name}': {e}")
                    
        if len(risk_multipliers) != len(strategies):
            raise ValueError(
                "Length of risk_multipliers must match number of strategies"
            )
            
        super().__init__(config, strategies)
        self.vix_data = vix_data.sort_index()
        self.risk_multipliers = risk_multipliers
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
                    # Formula: W_i = Target_Vol / (N * VIX * Risk_Multiplier_i)
                    num_strategies = len(self.strategies)
                    weights = []
                    for flag in self.risk_multipliers:
                        w = self.target_vol / (num_strategies * vix * flag)
                        weights.append(w)
                    
                    # Cap total risky weight by max_leverage
                    total_risky = sum(weights)
                    if total_risky > self.max_leverage:
                        scale = self.max_leverage / total_risky
                        weights = [w * scale for w in weights]
                        
                        # Iteratively shift capital from lowest vol to highest vol 
                        # to achieve Target_Vol or become 100% concentrated
                        while True:
                            current_vol = sum(w * vix * f for w, f in zip(weights, self.risk_multipliers))
                            if current_vol >= self.target_vol - 1e-6:
                                break
                                
                            # Find asset with highest flag
                            max_flag_idx = -1
                            max_flag = -1.0
                            for i, f in enumerate(self.risk_multipliers):
                                if f > max_flag:
                                    max_flag = f
                                    max_flag_idx = i
                                    
                            # Find asset with lowest flag that still has weight > 0
                            min_flag_idx = -1
                            min_flag = float('inf')
                            for i, (f, w) in enumerate(zip(self.risk_multipliers, weights)):
                                if i != max_flag_idx and w > 1e-6 and f < min_flag:
                                    min_flag = f
                                    min_flag_idx = i
                                    
                            if min_flag_idx == -1 or max_flag <= min_flag + 1e-9:
                                break  # Cannot shift anymore
                                
                            delta_vol = self.target_vol - current_vol
                            vol_increase_per_unit = vix * (max_flag - min_flag)
                            
                            shift = delta_vol / vol_increase_per_unit
                            actual_shift = min(shift, weights[min_flag_idx])
                            
                            weights[min_flag_idx] -= actual_shift
                            weights[max_flag_idx] += actual_shift
                    
                    # Update current weights cache
                    new_weights = {}
                    for i, strategy in enumerate(self.strategies):
                        new_weights[strategy.name] = weights[i]
                    
                    total_risky_capped = sum(weights)
                    new_weights[CASH_STRATEGY_NAME] = 1.0 - total_risky_capped
                    
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
