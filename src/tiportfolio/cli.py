"""TiPortfolio CLI — run backtests from the command line."""
from __future__ import annotations

import functools
import re
from pathlib import Path
from typing import Any

import click
import pandas as pd

import tiportfolio as ti


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_lookback(value: str) -> pd.DateOffset:
    """Parse a lookback string like '90d', '6m', '1y' into pd.DateOffset."""
    m = re.fullmatch(r"(\d+)([dmy])", value.strip().lower())
    if not m:
        raise click.BadParameter(f"Invalid lookback format: {value!r}. Use Nd, Nm, or Ny.")
    n = int(m.group(1))
    unit = m.group(2)
    if unit == "d":
        return pd.DateOffset(days=n)
    if unit == "m":
        return pd.DateOffset(months=n)
    return pd.DateOffset(years=n)


def _build_csv_map(csv_dir: str, tickers: list[str]) -> dict[str, str]:
    """Build a ticker → csv path dict from a directory."""
    path = Path(csv_dir)
    if not path.is_dir():
        raise click.BadParameter(f"CSV directory not found: {csv_dir}")
    result: dict[str, str] = {}
    for ticker in tickers:
        clean = ticker.lower().replace("^", "")
        candidates = sorted(path.glob(f"{clean}*.csv"))
        if candidates:
            result[ticker] = str(candidates[0])
    return result


def _build_select(select: str, top_n: int | None, lookback: str | None) -> Any:
    """Parse --select flag into a Select algo."""
    if select == "all":
        return ti.Select.All()
    if select == "momentum":
        if top_n is None:
            raise click.UsageError("--top-n is required with --select momentum")
        lb = _parse_lookback(lookback) if lookback else pd.DateOffset(days=60)
        return ti.Select.Momentum(n=top_n, lookback=lb)
    raise click.BadParameter(f"Unknown select strategy: {select!r}")


def _build_weigh(
    ratio: str,
    tickers: list[str],
    lookback: str | None,
    target_hv: float | None,
) -> Any:
    """Parse --ratio flag into a Weigh algo."""
    if ratio == "equal":
        return ti.Weigh.Equally()
    if ratio == "erc":
        lb = _parse_lookback(lookback) if lookback else pd.DateOffset(days=60)
        return ti.Weigh.ERC(lookback=lb)
    if ratio == "hv":
        if target_hv is None:
            raise click.UsageError("--target-hv is required with --ratio hv")
        lb = _parse_lookback(lookback) if lookback else pd.DateOffset(days=60)
        initial = {t: 1.0 / len(tickers) for t in tickers}
        return ti.Weigh.BasedOnHV(initial_ratio=initial, target_hv=target_hv, lookback=lb)
    # Try parsing as comma-separated floats
    try:
        weights_list = [float(x.strip()) for x in ratio.split(",")]
    except ValueError:
        raise click.BadParameter(f"Unknown ratio: {ratio!r}. Use equal, erc, hv, or comma-separated floats.")
    if len(weights_list) != len(tickers):
        raise click.BadParameter(
            f"Ratio count ({len(weights_list)}) does not match ticker count ({len(tickers)})"
        )
    return ti.Weigh.Ratio(dict(zip(tickers, weights_list)))


def _parse_leverage(value: str) -> float | list[float]:
    """Parse leverage: single float or comma-separated list."""
    parts = [x.strip() for x in value.split(",")]
    if len(parts) == 1:
        return float(parts[0])
    return [float(x) for x in parts]


def _run_backtest(
    signal: Any,
    tickers: str,
    start: str,
    end: str,
    ratio: str,
    select_: str,
    source: str,
    csv: str | None,
    capital: float,
    fee: float,
    rf: float,
    leverage: str,
    plot: str | None,
    full: bool,
    top_n: int | None,
    lookback: str | None,
    target_hv: float | None,
    aip: float | None,
    **_extra: Any,
) -> None:
    """Shared backtest runner for all subcommands."""
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]

    # Build data
    csv_map = _build_csv_map(csv, ticker_list) if csv else None
    data = ti.fetch_data(ticker_list, start=start, end=end, source=source, csv=csv_map)

    # Build algos
    select_algo = _build_select(select_, top_n, lookback)
    weigh_algo = _build_weigh(ratio, ticker_list, lookback, target_hv)
    algos = [signal, select_algo, weigh_algo, ti.Action.Rebalance()]

    # Build config
    config = ti.TiConfig(initial_capital=capital, fee_per_share=fee, risk_free_rate=rf)

    # Parse leverage
    lev = _parse_leverage(leverage)

    # Handle leverage list: create multiple identical backtests
    # Names stay as "portfolio" — _apply_leverage adds the suffix
    run_fn = ti.run_aip if aip and aip > 0 else ti.run
    aip_kwargs: dict[str, Any] = {"monthly_aip_amount": aip} if aip and aip > 0 else {}

    if isinstance(lev, list):
        backtests = []
        for _factor in lev:
            p = ti.Portfolio("portfolio", list(algos), list(ticker_list))
            backtests.append(ti.Backtest(p, data, config=config))
        result = run_fn(*backtests, leverage=lev, **aip_kwargs)
    else:
        portfolio = ti.Portfolio("portfolio", algos, ticker_list)
        bt = ti.Backtest(portfolio, data, config=config)
        result = run_fn(bt, leverage=lev, **aip_kwargs)

    # Output
    if full:
        click.echo(result.full_summary())
    else:
        click.echo(result.summary())

    if plot:
        fig = result.plot()
        fig.savefig(plot, dpi=150, bbox_inches="tight")
        click.echo(f"Chart saved to {plot}")


# ---------------------------------------------------------------------------
# Shared options decorator
# ---------------------------------------------------------------------------


def shared_options(f: Any) -> Any:
    """Apply all shared CLI options to a subcommand."""
    @click.option("--tickers", required=True, help="Comma-separated ticker symbols (e.g. QQQ,BIL,GLD)")
    @click.option("--start", required=True, help="Start date YYYY-MM-DD")
    @click.option("--end", required=True, help="End date YYYY-MM-DD")
    @click.option("--ratio", default="equal", help="Weighting: equal, 0.7,0.2,0.1, erc, hv")
    @click.option("--select", "select_", default="all", help="Selection: all, momentum")
    @click.option("--source", default="yfinance", help="Data source: yfinance, alpaca")
    @click.option("--csv", default=None, help="CSV directory for offline data")
    @click.option("--capital", default=10_000.0, type=float, help="Initial capital")
    @click.option("--fee", default=0.0035, type=float, help="Fee per share")
    @click.option("--rf", default=0.04, type=float, help="Risk-free rate")
    @click.option("--leverage", default="1.0", help="Leverage: single float or comma-separated list (e.g. 1.0,1.5,2.0)")
    @click.option("--plot", default=None, help="Save equity curve chart to file")
    @click.option("--full", is_flag=True, help="Print full summary instead of compact")
    @click.option("--top-n", default=None, type=int, help="Top-N for momentum selection")
    @click.option("--lookback", default=None, help="Lookback period: Nd, Nm, Ny (e.g. 90d, 6m)")
    @click.option("--target-hv", default=None, type=float, help="Target historical volatility for --ratio hv")
    @click.option("--aip", default=None, type=float, help="Monthly AIP amount — auto investment plan (cash added each month-end)")
    @functools.wraps(f)
    def wrapper(**kwargs: Any) -> Any:
        return f(**kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# CLI group and subcommands
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """TiPortfolio — run backtests from the command line."""


@cli.command()
@shared_options
@click.option("--day", default="end", help="Day within month: start, mid, end")
def monthly(day: str, **kwargs: Any) -> None:
    """Monthly rebalance strategy."""
    _run_backtest(ti.Signal.Monthly(day=day), **kwargs)


@cli.command()
@shared_options
@click.option("--day", default="end", help="Day within quarter: start, mid, end")
@click.option("--months", default=None, help="Comma-separated months (e.g. 3,6,9,12)")
def quarterly(day: str, months: str | None, **kwargs: Any) -> None:
    """Quarterly rebalance strategy."""
    month_list = [int(m.strip()) for m in months.split(",")] if months else None
    if month_list:
        signal = ti.Signal.Quarterly(months=month_list, day=day)
    else:
        signal = ti.Signal.Quarterly(day=day)
    _run_backtest(signal, **kwargs)


@cli.command()
@shared_options
@click.option("--day", default="end", help="Day within week: start, mid, end")
def weekly(day: str, **kwargs: Any) -> None:
    """Weekly rebalance strategy."""
    _run_backtest(ti.Signal.Weekly(day=day), **kwargs)


@cli.command()
@shared_options
@click.option("--day", default="end", help="Day within year: start, mid, end")
@click.option("--month", default=None, type=int, help="Month for yearly signal (1-12)")
def yearly(day: str, month: int | None, **kwargs: Any) -> None:
    """Yearly rebalance strategy."""
    if month:
        signal = ti.Signal.Yearly(day=day, month=month)
    else:
        signal = ti.Signal.Yearly(day=day)
    _run_backtest(signal, **kwargs)


@cli.command()
@shared_options
@click.option("--n", required=True, type=int, help="Fire every N periods")
@click.option("--period", required=True, help="Period: day, week, month, year")
@click.option("--day", default="end", help="Day within period: start, mid, end")
def every(n: int, period: str, day: str, **kwargs: Any) -> None:
    """Every-N-periods rebalance strategy."""
    _run_backtest(ti.Signal.EveryNPeriods(n=n, period=period, day=day), **kwargs)


@cli.command()
@shared_options
def once(**kwargs: Any) -> None:
    """Buy-and-hold (rebalance once)."""
    _run_backtest(ti.Signal.Once(), **kwargs)
