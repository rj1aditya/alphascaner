"""Tests for incremental market-data refreshes."""

from datetime import date
from pathlib import Path

import pandas as pd
from app.data.service import MarketDataService
from app.data.storage import PriceStore


class FakeProvider:
    """Deterministic provider used to test the application use case."""

    name = "fixture"

    def __init__(self) -> None:
        self.calls: list[tuple[str, date, date]] = []

    def fetch_daily(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        self.calls.append((symbol, start, end))
        index = pd.date_range(start, end, freq="D", name="date")
        return pd.DataFrame(
            {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "adj_close": 1.5, "volume": 100},
            index=index,
        )


def test_update_persists_and_then_requests_only_missing_dates(tmp_path: Path) -> None:
    """A subsequent refresh begins immediately after the latest stored bar."""
    provider = FakeProvider()
    store = PriceStore(tmp_path / "data", tmp_path / "data" / "database.duckdb", "zstd")
    service = MarketDataService(provider, store)

    first = service.update("RELIANCE", date(2024, 1, 1), date(2024, 1, 3))
    second = service.update("RELIANCE", date(2024, 1, 1), date(2024, 1, 5))

    assert first.rows_written == 3
    assert second.rows_written == 2
    assert provider.calls[-1] == ("RELIANCE", date(2024, 1, 4), date(2024, 1, 5))
    assert len(store.read("RELIANCE")) == 5
