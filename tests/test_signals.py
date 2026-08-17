"""Tests for initial pattern signals."""

import pandas as pd
from app.patterns.signals import SignalEngine, SignalLabel


def test_detects_breakout_and_golden_cross() -> None:
    """A volume-confirmed range escape and MA crossover are both surfaced."""
    frame = pd.DataFrame(
        {
            "close": [100.0] * 20 + [110.0],
            "high": [102.0] * 20 + [111.0],
            "low": [98.0] * 20 + [109.0],
            "volume_ratio": [1.0] * 20 + [2.0],
            "atr_14": [2.0] * 21,
            "sma_50": [99.0] * 20 + [101.0],
            "sma_200": [100.0] * 21,
        }
    )
    labels = {signal.label for signal in SignalEngine().detect(frame)}
    assert SignalLabel.BREAKOUT in labels
    assert SignalLabel.GOLDEN_CROSS in labels


def test_extended_pattern_paths_are_evaluated() -> None:
    """Long enriched series exercises geometric, contraction, and continuation rules."""
    close = [100.0 + index * 0.4 for index in range(60)]
    high = [value + (5 if index < 5 else 1) for index, value in enumerate(close)]
    low = [value - (5 if index < 5 else 1) for index, value in enumerate(close)]
    frame = pd.DataFrame(
        {
            "close": close,
            "high": high,
            "low": low,
            "volume": [2_000] * 5 + [500] * 55,
            "volume_ratio": [1.0] * 60,
            "atr_14": [1.0] * 60,
            "sma_50": [99.0] * 60,
            "sma_200": [98.0] * 60,
            "high_52w": close,
        }
    )
    labels = {signal.label for signal in SignalEngine().detect(frame)}
    assert SignalLabel.FIFTY_TWO_WEEK_BREAKOUT in labels
    assert SignalLabel.TREND_CONTINUATION in labels
