"""Tests for dashboard data discovery."""

from pathlib import Path
from unittest.mock import MagicMock

import app.dashboard.main as dashboard
import pandas as pd
from app.dashboard.main import _latest_report


def test_latest_report_returns_latest_parquet_report(tmp_path: Path) -> None:
    """The dashboard selects the newest ranked Parquet report."""
    reports = tmp_path / "reports"
    reports.mkdir()
    first = reports / "ranked_20260101_000000.parquet"
    latest = reports / "ranked_20260102_000000.parquet"
    first.touch()
    latest.touch()

    assert _latest_report(tmp_path) == latest


def test_latest_report_returns_none_without_reports(tmp_path: Path) -> None:
    """An empty data directory has no dashboard report source."""
    assert _latest_report(tmp_path) is None


def test_run_shows_empty_state_when_no_report(monkeypatch: object) -> None:
    """The dashboard provides guidance when no ranked report exists."""
    info = MagicMock()
    monkeypatch.setattr(dashboard, "_latest_report", lambda _: None)
    monkeypatch.setattr(dashboard.st, "set_page_config", MagicMock())
    monkeypatch.setattr(dashboard.st, "title", MagicMock())
    monkeypatch.setattr(dashboard.st, "caption", MagicMock())
    monkeypatch.setattr(dashboard.st, "info", info)

    dashboard.run()

    info.assert_called_once()


def test_run_renders_report_and_price_chart(monkeypatch: object) -> None:
    """The populated dashboard renders ranking and selected-symbol charts."""
    report = pd.DataFrame({"symbol": ["RELIANCE"], "score": [75.0]})
    indicators = pd.DataFrame(
        {
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.5],
            "sma_20": [99.0],
            "sma_50": [98.0],
            "rolling_high_20": [101.0],
            "rolling_low_20": [99.0],
            "rsi_14": [60.0],
            "macd": [1.0],
            "macd_signal": [0.8],
        },
        index=pd.DatetimeIndex(["2025-01-01"]),
    )
    monkeypatch.setattr(dashboard, "_latest_report", lambda _: Path("report.parquet"))
    monkeypatch.setattr(
        dashboard.pd,
        "read_parquet",
        lambda path: indicators if "indicators" in str(path) else report,
    )
    monkeypatch.setattr(dashboard.st, "set_page_config", MagicMock())
    monkeypatch.setattr(dashboard.st, "title", MagicMock())
    monkeypatch.setattr(dashboard.st, "caption", MagicMock())
    monkeypatch.setattr(dashboard.st.sidebar, "text_input", lambda *_: "")
    monkeypatch.setattr(dashboard.st.sidebar, "slider", lambda *args: args[-1])
    monkeypatch.setattr(dashboard.st.sidebar, "multiselect", lambda *args, **kwargs: ["RELIANCE"])
    monkeypatch.setattr(dashboard.st, "metric", MagicMock())
    monkeypatch.setattr(dashboard.st, "dataframe", MagicMock())
    monkeypatch.setattr(dashboard.st, "columns", lambda _: [MagicMock(), MagicMock(), MagicMock()])
    monkeypatch.setattr(dashboard.st, "bar_chart", MagicMock())
    monkeypatch.setattr(dashboard.st, "line_chart", MagicMock())
    charts = MagicMock()
    monkeypatch.setattr(dashboard.st, "plotly_chart", charts)
    monkeypatch.setattr(dashboard.st, "selectbox", lambda *_: "RELIANCE")

    dashboard.run()

    assert charts.call_count == 3
