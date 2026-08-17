"""Tests for trend classification."""

import pandas as pd
from app.patterns.trend import StructureLabel, TrendEngine, TrendLabel


def test_classifies_strong_uptrend() -> None:
    """Aligned moving averages with strong ADX produce a strong uptrend."""
    frame = pd.DataFrame(
        {
            "close": [120] * 20,
            "sma_20": [110] * 20,
            "sma_50": [100] * 20,
            "sma_200": [90] * 20,
            "adx_14": [30] * 20,
            "rolling_high_20": [125] * 20,
            "rolling_low_20": [95] * 20,
            "high": list(range(100, 120)),
            "low": list(range(80, 100)),
        }
    )
    result = TrendEngine().classify(frame)
    assert result.trend is TrendLabel.STRONG_UPTREND
    assert result.structure is StructureLabel.HIGHER_HIGH_HIGHER_LOW
