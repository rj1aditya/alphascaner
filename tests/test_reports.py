"""Tests for report exports."""

from pathlib import Path

import pandas as pd
from app.reports.service import ReportService
from app.scoring.engine import StockScore


class FakeScoringService:
    """Minimal ranking source for report tests."""

    def rank(self, symbols: list[str]) -> list[StockScore]:
        return [StockScore(symbols[0], 80, 20, 10, 20, 10, 10, 10)]


def test_generate_writes_all_report_formats(tmp_path: Path) -> None:
    """CSV, Parquet, and Excel ranked reports are written."""
    root = tmp_path / "data"
    indicator_root = root / "processed" / "indicators"
    indicator_root.mkdir(parents=True)
    pd.DataFrame(
        {
            "close": [100.0],
            "sma_20": [99.0],
            "sma_50": [98.0],
            "sma_200": [90.0],
            "rsi_14": [60.0],
            "atr_14": [2.0],
            "volume_ratio": [1.5],
        }
    ).to_parquet(indicator_root / "RELIANCE.parquet")
    paths = ReportService(root, FakeScoringService()).generate(["RELIANCE"])
    assert all(path.exists() for path in paths.values())
