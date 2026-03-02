"""CLI entry point for tiportfolio."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tiportfolio import (
    FixRatio,
    Schedule,
    ScheduleBasedEngine,
    VixRegimeAllocation,
    VolatilityBasedEngine,
)
from tiportfolio.calendar import VALID_SCHEDULES
from tiportfolio.data import load_csvs

VOLATILITY_CHOICES = ("VIX", "VVIX", "RVX", "VXD")


def main() -> None:
    parser = argparse.ArgumentParser(description="TiPortfolio backtest CLI")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory containing CSV files. If omitted, data is fetched by symbols (Alpaca or Yahoo Finance).",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["SPY", "QQQ", "GLD"],
        help="Symbols to include (required when not using --data-dir)",
    )
    parser.add_argument(
        "--weights",
        nargs="+",
        default=["0.5", "0.3", "0.2"],
        help="Weights for each symbol (sum to 1.0); used for time-based schedules or as low-vol weights when vix_regime and no --low-vol-weights",
    )
    parser.add_argument(
        "--rebalance",
        choices=list(VALID_SCHEDULES),
        default="month_end",
        help="Rebalance schedule",
    )
    parser.add_argument(
        "--volatility-symbol",
        choices=VOLATILITY_CHOICES,
        default=None,
        help="Volatility index for vix_regime (required when --rebalance vix_regime)",
    )
    parser.add_argument(
        "--target-vix",
        type=float,
        default=None,
        help="Target VIX level for vix_regime (required when --rebalance vix_regime)",
    )
    parser.add_argument(
        "--lower-bound",
        type=float,
        default=None,
        help="Lower bound offset for vix_regime (required when --rebalance vix_regime)",
    )
    parser.add_argument(
        "--upper-bound",
        type=float,
        default=None,
        help="Upper bound offset for vix_regime (required when --rebalance vix_regime)",
    )
    parser.add_argument(
        "--high-vol-weights",
        nargs="+",
        default=None,
        help="Weights when VIX is high (vix_regime only; same length as --symbols)",
    )
    parser.add_argument(
        "--low-vol-weights",
        nargs="+",
        default=None,
        help="Weights when VIX is low (vix_regime only; same length as --symbols)",
    )
    parser.add_argument("--fee-per-share", type=float, default=0.0035, help="Fee in USD per share (default: 0.0035, IBKR-style)")
    parser.add_argument("--start", type=str, default=None, help="Start date (required when not using --data-dir)")
    parser.add_argument("--end", type=str, default=None, help="End date (required when not using --data-dir)")
    args = parser.parse_args()

    target_symbols = [s.upper() for s in args.symbols]
    is_vix_regime = args.rebalance == "vix_regime"

    if is_vix_regime:
        if args.volatility_symbol is None or args.target_vix is None or args.lower_bound is None or args.upper_bound is None:
            print("--rebalance vix_regime requires --volatility-symbol, --target-vix, --lower-bound, --upper-bound")
            sys.exit(1)
        high_list = args.high_vol_weights
        low_list = args.low_vol_weights
        if high_list is None or low_list is None:
            print("--rebalance vix_regime requires --high-vol-weights and --low-vol-weights")
            sys.exit(1)
        high_list = [float(w) for w in high_list]
        low_list = [float(w) for w in low_list]
        if len(target_symbols) != len(high_list) or len(target_symbols) != len(low_list):
            print("--high-vol-weights and --low-vol-weights must have same length as --symbols")
            sys.exit(1)
        for name, wl in (("high-vol", high_list), ("low-vol", low_list)):
            if abs(sum(wl) - 1.0) > 0.01:
                print(f"--{name}-weights must sum to 1.0; got {sum(wl)}")
                sys.exit(1)
        high_weights = dict(zip(target_symbols, high_list))
        low_weights = dict(zip(target_symbols, low_list))
        allocation = VixRegimeAllocation(
            target_vix=args.target_vix,
            lower_bound=args.lower_bound,
            upper_bound=args.upper_bound,
            high_vol_allocation=FixRatio(weights=high_weights),
            low_vol_allocation=FixRatio(weights=low_weights),
        )
    else:
        weights_list = [float(w) for w in args.weights]
        if len(target_symbols) != len(weights_list):
            print("--symbols and --weights must have the same length")
            sys.exit(1)
        weight_sum = sum(weights_list)
        if abs(weight_sum - 1.0) > 0.01:
            print(f"Weights must sum to 1.0; got {weight_sum}")
            sys.exit(1)
        weights = dict(zip(target_symbols, weights_list))
        allocation = FixRatio(weights=weights)

    if args.data_dir is not None:
        # CSV mode: load from directory, then run via WithDataFetcher with dfs_in_dict
        symbols_for_data = allocation.get_symbols()
        paths = list(args.data_dir.glob("*.csv"))
        if not paths:
            print(f"No CSV files in {args.data_dir}")
            sys.exit(1)
        prices = load_csvs(paths)
        symbols_available = set(prices.keys())
        missing = set(symbols_for_data) - symbols_available
        if is_vix_regime:
            vol_missing = args.volatility_symbol not in symbols_available
            if missing or vol_missing:
                need = set(symbols_for_data) | {args.volatility_symbol}
                missing_all = need - symbols_available
                if missing_all:
                    print(f"Symbols/VIX not found in data: {missing_all}. Available: {sorted(symbols_available)}")
                    sys.exit(1)
        elif missing:
            print(f"Symbols not found in data: {missing}. Available: {sorted(symbols_available)}")
            sys.exit(1)
        if is_vix_regime:
            prices_sub = {s: prices[s] for s in symbols_for_data}
            prices_sub[args.volatility_symbol] = prices[args.volatility_symbol]
            prices = prices_sub
        else:
            prices = {s: prices[s] for s in symbols_for_data}
        if is_vix_regime:
            engine = VolatilityBasedEngine(
                allocation=allocation,
                rebalance=Schedule(args.rebalance),
                fee_per_share=args.fee_per_share,
            )
            try:
                result = engine.run(
                    symbols=target_symbols,
                    start=args.start,
                    end=args.end,
                    dfs_in_dict=prices,
                    volatility_symbol=args.volatility_symbol,
                    target_vix=args.target_vix,
                    lower_bound=args.lower_bound,
                    upper_bound=args.upper_bound,
                )
            except Exception as e:
                msg = str(e)
                if not msg.startswith("Failed to fetch data"):
                    msg = f"Failed to fetch data: {msg}"
                print(msg)
                sys.exit(1)
        else:
            engine = ScheduleBasedEngine(
                allocation=allocation,
                rebalance=Schedule(args.rebalance),
                fee_per_share=args.fee_per_share,
            )
            try:
                result = engine.run(
                    symbols=target_symbols,
                    start=args.start,
                    end=args.end,
                    dfs_in_dict=prices,
                )
            except Exception as e:
                msg = str(e)
                if not msg.startswith("Failed to fetch data"):
                    msg = f"Failed to fetch data: {msg}"
                print(msg)
                sys.exit(1)
    else:
        # Symbols mode: fetch data via Alpaca or Yahoo Finance
        if not args.symbols or args.start is None or args.end is None:
            print("--symbols, --start, and --end are required when not using --data-dir")
            sys.exit(1)
        if is_vix_regime:
            engine = VolatilityBasedEngine(
                allocation=allocation,
                rebalance=Schedule(args.rebalance),
                fee_per_share=args.fee_per_share,
            )
            try:
                result = engine.run(
                    symbols=target_symbols,
                    start=args.start,
                    end=args.end,
                    volatility_symbol=args.volatility_symbol,
                    target_vix=args.target_vix,
                    lower_bound=args.lower_bound,
                    upper_bound=args.upper_bound,
                )
            except Exception as e:
                msg = str(e)
                if not msg.startswith("Failed to fetch data"):
                    msg = f"Failed to fetch data: {msg}"
                print(msg)
                sys.exit(1)
        else:
            engine = ScheduleBasedEngine(
                allocation=allocation,
                rebalance=Schedule(args.rebalance),
                fee_per_share=args.fee_per_share,
            )
            try:
                result = engine.run(symbols=target_symbols, start=args.start, end=args.end)
            except Exception as e:
                msg = str(e)
                if not msg.startswith("Failed to fetch data"):
                    msg = f"Failed to fetch data: {msg}"
                print(msg)
                sys.exit(1)

    print(result.summary())


if __name__ == "__main__":
    main()
