"""Tests for Yahoo Finance normalization without network access."""

from datetime import date

import pandas as pd
from app.data.yahoo import YahooProvider


def test_yahoo_provider_normalizes_nse_ticker_and_columns(monkeypatch: object) -> None:
    """Yahoo responses are converted to the application's daily-bar schema."""
    captured: dict[str, object] = {}

    def download(ticker: str, **kwargs: object) -> pd.DataFrame:
        captured["ticker"] = ticker
        captured.update(kwargs)
        return pd.DataFrame(
            {
                "Open": [1.0],
                "High": [2.0],
                "Low": [0.5],
                "Close": [1.5],
                "Adj Close": [1.4],
                "Volume": [100],
            },
            index=pd.DatetimeIndex(["2024-01-01"], name="Date"),
        )

    monkeypatch.setattr("app.data.yahoo.yf.download", download)
    frame = YahooProvider().fetch_daily("RELIANCE", date(2024, 1, 1), date(2024, 1, 1))

    assert captured["ticker"] == "RELIANCE.NS"
    assert list(frame.columns) == ["open", "high", "low", "close", "adj_close", "volume"]
    assert frame.index.name == "date"
