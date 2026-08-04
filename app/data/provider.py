"""Provider contracts for historical market data."""

from __future__ import annotations

from datetime import date
from typing import Protocol

import pandas as pd


class MarketDataProvider(Protocol):
    """Port implemented by external market-data providers."""

    @property
    def name(self) -> str:
        """Return the provider's stable identifier."""

    def fetch_daily(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        """Fetch normalized daily OHLCV bars for an inclusive date interval."""
