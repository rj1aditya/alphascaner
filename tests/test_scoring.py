"""Tests for opportunity scoring."""

import pandas as pd
from app.scoring.engine import ScoreEngine


def test_scores_and_ranks_bullish_symbol() -> None:
    """A bullish, liquid, low-risk symbol receives a bounded positive score."""
    frame = pd.DataFrame(
        {
            "close": [110.0],
            "sma_50": [100.0],
            "sma_200": [90.0],
            "rsi_14": [60.0],
            "volume_ratio": [2.0],
            "relative_strength": [1.1],
            "atr_14": [2.0],
        }
    )
    engine = ScoreEngine()
    result = engine.score("RELIANCE", frame, {"breakout", "golden_cross"})
    assert 0 < result.total <= 100
    assert engine.rank([result, result])[0].symbol == "RELIANCE"
