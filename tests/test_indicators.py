"""Tests for the indicator engine."""

import pandas as pd
from app.indicators.engine import IndicatorEngine


def test_calculate_adds_core_indicators() -> None:
    """A sufficiently long OHLCV series produces primary feature columns."""
    index = pd.date_range("2023-01-01", periods=260, freq="D", name="date")
    close = pd.Series(range(100, 360), index=index, dtype=float)
    prices = pd.DataFrame(
        {
            "open": close - 1,
            "high": close + 2,
            "low": close - 2,
            "close": close,
            "adj_close": close,
            "volume": 1000,
        },
        index=index,
    )
    result = IndicatorEngine().calculate(prices, benchmark=close * 2)
    assert {
        "sma_20",
        "ema_200",
        "rsi_14",
        "macd",
        "atr_14",
        "obv",
        "bb_upper",
        "donchian_upper",
        "high_52w",
        "relative_strength",
    }.issubset(result.columns)
    assert result["sma_20"].iloc[-1] > 0
