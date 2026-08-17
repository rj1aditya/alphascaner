"""Tests for indicator refresh persistence."""

import pandas as pd
from app.data.storage import PriceStore
from app.indicators.engine import IndicatorEngine
from app.indicators.service import IndicatorRefreshService
from app.indicators.storage import IndicatorStore


def test_refresh_writes_processed_indicators(tmp_path: object) -> None:
    """Stored raw bars are transformed and persisted as processed indicators."""
    root = tmp_path / "data"
    prices = PriceStore(root, root / "database.duckdb", "zstd")
    index = pd.date_range("2023-01-01", periods=260, freq="D", name="date")
    close = pd.Series(range(100, 360), index=index, dtype=float)
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "adj_close": close,
            "volume": 1000,
        },
        index=index,
    )
    prices.upsert("RELIANCE", "fixture", frame)
    result = IndicatorRefreshService(
        prices, IndicatorEngine(), IndicatorStore(root, "zstd")
    ).refresh("RELIANCE")
    assert result.rows_processed == 260
    assert result.output_path.exists()
