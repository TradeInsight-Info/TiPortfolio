from __future__ import annotations

import pytest

from tiportfolio.config import TiConfig


class TestTiConfigDefaults:
    def test_default_fee_per_share(self) -> None:
        config = TiConfig()
        assert config.fee_per_share == 0.0035

    def test_default_risk_free_rate(self) -> None:
        config = TiConfig()
        assert config.risk_free_rate == 0.04

    def test_default_loan_rate(self) -> None:
        config = TiConfig()
        assert config.loan_rate == 0.0514

    def test_default_stock_borrow_rate(self) -> None:
        config = TiConfig()
        assert config.stock_borrow_rate == 0.07

    def test_default_initial_capital(self) -> None:
        config = TiConfig()
        assert config.initial_capital == 10_000

    def test_default_bars_per_year(self) -> None:
        config = TiConfig()
        assert config.bars_per_year == 252


class TestTiConfigCustom:
    def test_custom_fee(self) -> None:
        config = TiConfig(fee_per_share=0.01)
        assert config.fee_per_share == 0.01
        assert config.initial_capital == 10_000  # other defaults preserved

    def test_custom_initial_capital(self) -> None:
        config = TiConfig(initial_capital=50_000)
        assert config.initial_capital == 50_000

    def test_multiple_overrides(self) -> None:
        config = TiConfig(fee_per_share=0.0, initial_capital=100_000, bars_per_year=365)
        assert config.fee_per_share == 0.0
        assert config.initial_capital == 100_000
        assert config.bars_per_year == 365


class TestTiConfigFrozen:
    def test_cannot_mutate_field(self) -> None:
        config = TiConfig()
        with pytest.raises(AttributeError):
            config.fee_per_share = 0.99  # type: ignore[misc]
