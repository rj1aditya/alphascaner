"""Incremental daily-price refresh use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.data.provider import MarketDataProvider
from app.data.storage import PriceStore


@dataclass(frozen=True)
class UpdateResult:
    """Outcome of refreshing one instrument."""

    symbol: str
    rows_written: int
    start: date
    end: date


class MarketDataService:
    """Coordinate provider downloads and durable incremental storage."""

    def __init__(self, provider: MarketDataProvider, store: PriceStore) -> None:
        self._provider = provider
        self._store = store

    def update(self, symbol: str, start: date, end: date) -> UpdateResult:
        """Download only missing daily bars and atomically merge them into storage."""
        latest = self._store.latest_date(symbol)
        effective_start = max(start, latest + timedelta(days=1)) if latest else start
        if effective_start > end:
            return UpdateResult(symbol=symbol, rows_written=0, start=effective_start, end=end)
        bars = self._provider.fetch_daily(symbol, effective_start, end)
        return UpdateResult(
            symbol, self._store.upsert(symbol, self._provider.name, bars), effective_start, end
        )
