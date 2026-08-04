"""Yahoo Finance implementation of the market-data provider port."""

from __future__ import annotations

from datetime import date, timedelta
from typing import cast

import pandas as pd
import yfinance as yf

from app.data.provider import MarketDataProvider


class YahooProvider(MarketDataProvider):
    """Download daily NSE-adjusted OHLCV bars through Yahoo Finance."""

    def __init__(self, exchange_suffix: str = ".NS") -> None:
        self._exchange_suffix = exchange_suffix

    @property
    def name(self) -> str:
        """Return the provider identifier."""
        return "yahoo"

    def fetch_daily(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        """Fetch and normalize daily bars.

        Yahoo's end boundary is exclusive, so one day is added to preserve the
        provider contract's inclusive end date.
        """
        ticker = self._ticker(symbol)
        frame = yf.download(
            ticker,
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if frame.empty:
            return self._empty_frame()
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        normalized = frame.rename(
            columns={
                "Adj Close": "adj_close",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        normalized.index = pd.to_datetime(normalized.index, utc=True).tz_convert(None).normalize()
        normalized.index.name = "date"
        selected = normalized.loc[:, ["open", "high", "low", "close", "adj_close", "volume"]]
        return cast(pd.DataFrame, selected.astype({"volume": "int64"}))

    def _ticker(self, symbol: str) -> str:
        """Map NSE symbols to Yahoo tickers while preserving index tickers."""
        return (
            symbol
            if symbol.startswith("^") or symbol.endswith(self._exchange_suffix)
            else f"{symbol}{self._exchange_suffix}"
        )

    @staticmethod
    def _empty_frame() -> pd.DataFrame:
        """Create an empty normalized daily-bar frame."""
        frame = pd.DataFrame(columns=["open", "high", "low", "close", "adj_close", "volume"])
        frame.index = pd.DatetimeIndex([], name="date")
        return frame
