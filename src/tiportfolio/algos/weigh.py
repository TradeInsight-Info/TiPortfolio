from __future__ import annotations

import math

import numpy as np
import pandas as pd

from tiportfolio.algo import Algo, Context


class Weigh:
    """Namespace for weigh algos (how much to allocate)."""

    class Equally(Algo):
        """Divides capital equally across context.selected."""

        def __init__(self, short: bool = False) -> None:
            self._short = short

        def __call__(self, context: Context) -> bool:
            n = len(context.selected)
            if n == 0:
                return True
            sign = -1.0 if self._short else 1.0
            context.weights = {
                (item if isinstance(item, str) else item.name): sign / n
                for item in context.selected
            }
            return True

    class Ratio(Algo):
        """Assigns explicit weights, normalised to sum(|w|) = 1.0.

        Args:
            weights: Dict mapping ticker/name to target weight.
                     Tickers in selected but missing from weights get weight 0.
        """

        def __init__(self, weights: dict[str, float]) -> None:
            self._weights = weights

        def __call__(self, context: Context) -> bool:
            keys = [
                (item if isinstance(item, str) else item.name)
                for item in context.selected
            ]
            raw = {k: self._weights[k] for k in keys if k in self._weights}
            total = sum(abs(v) for v in raw.values()) or 1.0
            context.weights = {k: v / total for k, v in raw.items()}
            return True

    class BasedOnHV(Algo):
        """Scales initial_ratio to target annualised portfolio volatility.

        Uses diagonal covariance approximation:
        portfolio_hv = sqrt(sum((w * hv)^2))

        Args:
            initial_ratio: Starting weight allocation per ticker.
            target_hv: Target annualised volatility as decimal (0.15 = 15%).
            lookback: Window for computing historical volatility.
        """

        def __init__(
            self,
            initial_ratio: dict[str, float],
            target_hv: float,
            lookback: pd.DateOffset,
        ) -> None:
            self._initial_ratio = initial_ratio
            self._target_hv = target_hv
            self._lookback = lookback

        def __call__(self, context: Context) -> bool:
            start = context.date - self._lookback
            end = context.date
            bars_per_year = context.config.bars_per_year

            keys = [
                (item if isinstance(item, str) else item.name)
                for item in context.selected
            ]

            hv: dict[str, float] = {}
            for ticker in keys:
                if ticker not in context.prices:
                    continue
                series = context.prices[ticker].loc[start:end, "close"]
                daily_returns = series.pct_change().dropna()
                hv[ticker] = float(daily_returns.std() * math.sqrt(bars_per_year))

            # Diagonal covariance approximation
            portfolio_hv = math.sqrt(
                sum(
                    (self._initial_ratio.get(t, 0.0) * hv.get(t, 0.0)) ** 2
                    for t in keys
                )
            )

            if portfolio_hv == 0.0:
                context.weights = dict(self._initial_ratio)
                return True

            scale = self._target_hv / portfolio_hv
            context.weights = {
                t: self._initial_ratio.get(t, 0.0) * scale for t in keys
            }
            return True

    class BasedOnBeta(Algo):
        """Scales initial_ratio weights to achieve a target portfolio beta.

        Computes per-asset beta against a benchmark using OLS over the lookback
        window, then iteratively adjusts weights until portfolio beta converges
        to the target.

        Args:
            initial_ratio: Starting weight allocation per ticker.
            target_beta: Target portfolio beta (0 = market-neutral).
            lookback: Window for computing rolling betas.
            base_data: Benchmark OHLCV DataFrame (e.g. SPY), passed directly.
        """

        _MAX_ITERATIONS: int = 1000
        _TOLERANCE: float = 1e-6

        def __init__(
            self,
            initial_ratio: dict[str, float],
            target_beta: float,
            lookback: pd.DateOffset,
            base_data: pd.DataFrame,
        ) -> None:
            self._initial_ratio = initial_ratio
            self._target_beta = target_beta
            self._lookback = lookback
            self._base_data = base_data

        def _compute_beta(
            self, asset_returns: pd.Series, benchmark_returns: pd.Series  # type: ignore[type-arg]
        ) -> float:
            """Beta = Cov(r_asset, r_bench) / Var(r_bench)."""
            aligned = pd.concat(
                [asset_returns, benchmark_returns], axis=1, join="inner"
            ).dropna()
            if len(aligned) < 2:
                return 0.0
            cov_matrix = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
            var_bench = cov_matrix[1, 1]
            if var_bench == 0.0:
                return 0.0
            return float(cov_matrix[0, 1] / var_bench)

        def __call__(self, context: Context) -> bool:
            start = context.date - self._lookback
            end = context.date

            # Validate benchmark data coverage
            bench_data = self._base_data.loc[start:end]
            if len(bench_data) < 2:
                raise ValueError(
                    f"Insufficient benchmark data for lookback window "
                    f"[{start} .. {end}]: got {len(bench_data)} rows, need >= 2"
                )

            bench_returns = bench_data["close"].pct_change().dropna()

            keys = [
                (item if isinstance(item, str) else item.name)
                for item in context.selected
            ]

            # Compute per-asset betas
            betas: dict[str, float] = {}
            for ticker in keys:
                if ticker not in context.prices:
                    betas[ticker] = 0.0
                    continue
                series = context.prices[ticker].loc[start:end, "close"]
                asset_returns = series.pct_change().dropna()
                betas[ticker] = self._compute_beta(asset_returns, bench_returns)

            # Iterative scaling toward target beta
            weights = {t: self._initial_ratio.get(t, 0.0) for t in keys}

            for _ in range(self._MAX_ITERATIONS):
                portfolio_beta = sum(weights[t] * betas[t] for t in keys)
                error = portfolio_beta - self._target_beta

                if abs(error) < self._TOLERANCE:
                    break

                # Distribute error reduction proportionally to beta contributions
                beta_contrib_sum = sum(abs(betas[t]) for t in keys)
                if beta_contrib_sum == 0.0:
                    break  # all zero-beta assets, nothing to adjust

                for t in keys:
                    if betas[t] == 0.0:
                        continue
                    adjustment = error * (abs(betas[t]) / beta_contrib_sum)
                    if betas[t] != 0.0:
                        weights[t] -= adjustment / betas[t]

            context.weights = {t: float(w) for t, w in weights.items()}
            return True

    class ERC(Algo):
        """Equal Risk Contribution (Risk Parity) weighting.

        Sizes each asset so every position contributes the same amount of risk
        to the total portfolio. Delegates optimisation to riskfolio-lib.

        Args:
            lookback: Window for computing the covariance matrix.
            covar_method: Covariance estimation method — "ledoit-wolf", "hist", or "oas".
            risk_parity_method: Solver — "ccd" or "slsqp" (unused directly; riskfolio uses its own solver).
            maximum_iterations: Max solver iterations.
            tolerance: Convergence tolerance.
        """

        _COVAR_MAP: dict[str, str] = {
            "ledoit-wolf": "ledoit",
            "hist": "hist",
            "oas": "oas",
        }

        def __init__(
            self,
            lookback: pd.DateOffset,
            covar_method: str = "ledoit-wolf",
            risk_parity_method: str = "ccd",
            maximum_iterations: int = 100,
            tolerance: float = 1e-8,
        ) -> None:
            self._lookback = lookback
            self._covar_method = covar_method
            self._risk_parity_method = risk_parity_method
            self._maximum_iterations = maximum_iterations
            self._tolerance = tolerance

        def __call__(self, context: Context) -> bool:
            import riskfolio

            start = context.date - self._lookback
            end = context.date

            keys = [
                (item if isinstance(item, str) else item.name)
                for item in context.selected
            ]

            # Build returns DataFrame over lookback window
            returns_dict: dict[str, pd.Series] = {}  # type: ignore[type-arg]
            for ticker in keys:
                if ticker not in context.prices:
                    raise ValueError(
                        f"Insufficient data for '{ticker}': not found in prices"
                    )
                series = context.prices[ticker].loc[start:end, "close"]
                rets = series.pct_change().dropna()
                if len(rets) < 2:
                    raise ValueError(
                        f"Insufficient data for '{ticker}' in lookback window "
                        f"[{start} .. {end}]: got {len(rets)} return observations, need >= 2"
                    )
                returns_dict[ticker] = rets

            returns_df = pd.DataFrame(returns_dict)
            returns_df = returns_df.dropna()

            if len(returns_df) < 2:
                raise ValueError(
                    f"Insufficient overlapping data for covariance estimation: "
                    f"got {len(returns_df)} rows, need >= 2"
                )

            # Use riskfolio-lib for risk parity optimisation
            rfl_covar = self._COVAR_MAP.get(self._covar_method, "hist")

            port = riskfolio.Portfolio(returns=returns_df)
            port.assets_stats(method_mu="hist", method_cov=rfl_covar)

            weights_df = port.rp_optimization(model="Classic", rm="MV")

            if weights_df is None or weights_df.empty:
                raise ValueError(
                    "Risk parity solver failed to converge"
                )

            # Extract weights and normalise to exactly 1.0
            raw_weights = weights_df["weights"].to_dict()
            total = sum(raw_weights.values())
            if total == 0.0:
                raise ValueError("Risk parity solver returned all-zero weights")

            context.weights = {k: float(v / total) for k, v in raw_weights.items()}
            return True
