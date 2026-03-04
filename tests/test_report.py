"""Tests for report module: summary_table, rebalance_decisions_table, compare_strategies."""

import pytest
import pandas as pd

from tiportfolio.backtest import BacktestResult
from tiportfolio.report import compare_strategies, plot_strategy_comparison_interactive

_TOP5 = ["sharpe_ratio", "sortino_ratio", "mar_ratio", "cagr", "max_drawdown"]


def _make_result(metrics: dict, equity: pd.Series | None = None) -> BacktestResult:
    if equity is None:
        equity = pd.Series(
            [100.0, 102.0, 101.0],
            index=pd.DatetimeIndex(["2019-01-01", "2019-01-02", "2019-01-03"], tz="UTC"),
        )
    return BacktestResult(equity_curve=equity, metrics=metrics, rebalance_decisions=[])


# ---------------------------------------------------------------------------
# Existing tests (unleveraged)
# ---------------------------------------------------------------------------

def test_compare_strategies_returns_top5_rows():
    """compare_strategies returns exactly 5 rows with the canonical top-5 index."""
    metrics_a = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    metrics_b = {"sharpe_ratio": 0.8, "sortino_ratio": 1.2, "mar_ratio": 0.48, "cagr": 0.12, "max_drawdown": 0.25}
    result_a = _make_result(metrics_a)
    result_b = _make_result(metrics_b)

    df = compare_strategies(result_a, result_b, names=["A", "B"])

    assert list(df.index) == _TOP5
    assert len(df) == 5
    assert list(df.columns) == ["A", "B", "better"]


def test_compare_strategies_better_column():
    """compare_strategies correctly identifies the better strategy per metric."""
    metrics_a = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    metrics_b = {"sharpe_ratio": 0.8, "sortino_ratio": 1.2, "mar_ratio": 0.48, "cagr": 0.12, "max_drawdown": 0.15}
    result_a = _make_result(metrics_a)
    result_b = _make_result(metrics_b)

    df = compare_strategies(result_a, result_b, names=["A", "B"])

    assert df.loc["sharpe_ratio", "better"] == "A"
    assert df.loc["sortino_ratio", "better"] == "A"   # higher is better
    assert df.loc["mar_ratio", "better"] == "A"
    assert df.loc["cagr", "better"] == "B"
    assert df.loc["max_drawdown", "better"] == "B"    # lower is better


def test_compare_strategies_tie():
    """compare_strategies reports 'tie' when two strategies have equal metric values."""
    metrics = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    result_a = _make_result(metrics)
    result_b = _make_result(metrics)

    df = compare_strategies(result_a, result_b, names=["A", "B"])

    for metric in _TOP5:
        assert df.loc[metric, "better"] == "tie"


# ---------------------------------------------------------------------------
# Task 4.1 – scalar leverage adjusts metrics, Sharpe/Sortino unchanged
# ---------------------------------------------------------------------------

def test_compare_strategies_scalar_leverage_adjusts_metrics():
    """Scalar leverage scales max_drawdown, adjusts cagr, recomputes mar_ratio; Sharpe/Sortino unchanged."""
    metrics = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    result = _make_result(metrics)

    df = compare_strategies(result, names=["A"], leverages=1.5, yearly_loan_rates=0.0)

    assert df.loc["max_drawdown", "A"] == pytest.approx(0.30)           # 1.5 * 0.20
    assert df.loc["cagr", "A"] == pytest.approx(0.15)                   # 1.5 * 0.10
    assert df.loc["mar_ratio", "A"] == pytest.approx(0.15 / 0.30)       # lev_cagr / lev_dd
    assert df.loc["sharpe_ratio", "A"] == pytest.approx(1.0)            # unchanged
    assert df.loc["sortino_ratio", "A"] == pytest.approx(1.5)           # unchanged


# ---------------------------------------------------------------------------
# Task 4.2 – per-strategy leverage list: only second strategy adjusted
# ---------------------------------------------------------------------------

def test_compare_strategies_per_strategy_leverage():
    """Per-strategy leverage list: only the leveraged strategy has adjusted metrics."""
    metrics = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    result_a = _make_result(metrics)
    result_b = _make_result(metrics)

    df = compare_strategies(result_a, result_b, names=["A", "B"], leverages=[1.0, 1.5])

    # A is unleveraged — original values
    assert df.loc["max_drawdown", "A"] == pytest.approx(0.20)
    assert df.loc["cagr", "A"] == pytest.approx(0.10)
    # B is leveraged
    assert df.loc["max_drawdown", "B (L1.5x)"] == pytest.approx(0.30)
    assert df.loc["cagr", "B (L1.5x)"] == pytest.approx(0.15)


# ---------------------------------------------------------------------------
# Tasks 4.3 & 4.4 – ValueError on mismatched list length
# ---------------------------------------------------------------------------

def test_compare_strategies_leverages_list_length_mismatch_raises():
    result = _make_result({"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20})
    with pytest.raises(ValueError, match="leverages"):
        compare_strategies(result, names=["A"], leverages=[1.0, 1.5])


def test_compare_strategies_loan_rates_list_length_mismatch_raises():
    result = _make_result({"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20})
    with pytest.raises(ValueError, match="yearly_loan_rates"):
        compare_strategies(result, names=["A"], yearly_loan_rates=[0.05, 0.03])


# ---------------------------------------------------------------------------
# Task 4.5 – column header decoration (leverage only)
# ---------------------------------------------------------------------------

def test_compare_strategies_column_decoration_leverage_only():
    """Leveraged column gets (L1.5x) suffix; unleveraged column unchanged."""
    metrics = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    r_a = _make_result(metrics)
    r_b = _make_result(metrics)

    df = compare_strategies(r_a, r_b, names=["A", "B"], leverages=[1.0, 1.5])

    assert "A" in df.columns
    assert "B (L1.5x)" in df.columns
    assert "B" not in df.columns


# ---------------------------------------------------------------------------
# Task 4.6 – column header decoration with loan rate
# ---------------------------------------------------------------------------

def test_compare_strategies_column_decoration_with_loan_rate():
    """Column decorated with (L1.5x, r5.0%) when both leverage and loan rate set."""
    metrics = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    result = _make_result(metrics)

    df = compare_strategies(result, names=["A"], leverages=1.5, yearly_loan_rates=0.05)

    assert "A (L1.5x, r5.0%)" in df.columns


# ---------------------------------------------------------------------------
# Task 4.7 – default (no leverage) is identical to current behaviour
# ---------------------------------------------------------------------------

def test_compare_strategies_default_identical_to_unleveraged():
    """Default params (leverage=1.0, rate=0.0) produce same output as before."""
    metrics_a = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    metrics_b = {"sharpe_ratio": 0.8, "sortino_ratio": 1.2, "mar_ratio": 0.48, "cagr": 0.12, "max_drawdown": 0.25}
    r_a = _make_result(metrics_a)
    r_b = _make_result(metrics_b)

    df_default = compare_strategies(r_a, r_b, names=["A", "B"])
    df_explicit = compare_strategies(r_a, r_b, names=["A", "B"], leverages=1.0, yearly_loan_rates=0.0)

    assert list(df_default.columns) == ["A", "B", "better"]
    pd.testing.assert_frame_equal(df_default, df_explicit)


# ---------------------------------------------------------------------------
# Task 6.1 – chart: default params produce original curves, undecorated names
# ---------------------------------------------------------------------------

def test_chart_default_params_match_original_curves():
    """Default leverage produces trace Y-values equal to original equity curves and undecorated names."""
    equity_a = pd.Series(
        [100.0, 105.0, 103.0, 108.0],
        index=pd.DatetimeIndex(["2019-01-01", "2019-01-02", "2019-01-03", "2019-01-04"], tz="UTC"),
    )
    equity_b = pd.Series(
        [100.0, 102.0, 99.0, 101.0],
        index=pd.DatetimeIndex(["2019-01-01", "2019-01-02", "2019-01-03", "2019-01-04"], tz="UTC"),
    )
    metrics = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    r_a = _make_result(metrics, equity_a)
    r_b = _make_result(metrics, equity_b)

    fig = plot_strategy_comparison_interactive(r_a, r_b, names=["A", "B"])

    trace_a = fig.data[0]
    trace_b = fig.data[1]
    assert trace_a.name == "A"
    assert trace_b.name == "B"
    assert list(trace_a.y) == pytest.approx(list(equity_a.values))
    assert list(trace_b.y) == pytest.approx(list(equity_b.values))


# ---------------------------------------------------------------------------
# Task 6.2 – chart: leverage preserves starting equity, changes subsequent values
# ---------------------------------------------------------------------------

def test_chart_leveraged_curve_preserves_start_and_diverges():
    """Leveraged trace starts at same equity; subsequent values differ from raw."""
    equity = pd.Series(
        [100.0, 102.0, 101.0, 104.0],
        index=pd.DatetimeIndex(["2019-01-01", "2019-01-02", "2019-01-03", "2019-01-04"], tz="UTC"),
    )
    metrics = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    result = _make_result(metrics, equity)

    fig = plot_strategy_comparison_interactive(result, names=["A"], leverages=1.5)

    trace = fig.data[0]
    assert trace.y[0] == pytest.approx(100.0)                # starting equity preserved
    assert trace.y[1] != pytest.approx(equity.values[1])     # subsequent values differ
    assert trace.name == "A (L1.5x)"


# ---------------------------------------------------------------------------
# Task 6.3 – chart: ValueError on mismatched leverages list
# ---------------------------------------------------------------------------

def test_chart_leverages_list_length_mismatch_raises():
    metrics = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    result = _make_result(metrics)
    with pytest.raises(ValueError, match="leverages"):
        plot_strategy_comparison_interactive(result, leverages=[1.0, 1.5])
