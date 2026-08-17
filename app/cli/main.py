"""Typer command-line entry point."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from loguru import logger

from app import __version__
from app.config.settings import Settings, load_settings
from app.core.logging import configure_logging
from app.data.service import MarketDataService
from app.data.storage import PriceStore
from app.data.yahoo import YahooProvider
from app.indicators.engine import IndicatorEngine
from app.indicators.service import IndicatorRefreshService
from app.indicators.storage import IndicatorStore
from app.patterns.service import PatternAnalysisService
from app.patterns.signals import SignalEngine
from app.patterns.trend import TrendEngine
from app.reports.service import ReportService
from app.scoring.engine import ScoreEngine
from app.scoring.service import ScoringService

app = typer.Typer(
    name="alphascanner", help="Professional NSE positional trading scanner.", no_args_is_help=True
)
config_app = typer.Typer(help="Inspect AlphaScanner runtime configuration.", no_args_is_help=True)
app.add_typer(config_app, name="config")


def _settings_as_json(settings: Settings) -> str:
    """Serialize settings in a stable, human-readable JSON representation."""
    return json.dumps(settings.model_dump(mode="json"), indent=2, sort_keys=True)


@app.callback()
def initialise() -> None:
    """Configure application services before executing a CLI command."""
    configure_logging(load_settings().application)


@app.command()
def version() -> None:
    """Print the installed AlphaScanner version."""
    typer.echo(__version__)


@app.command()
def update(
    symbols: Annotated[
        list[str], typer.Argument(help="One or more NSE symbols, e.g. RELIANCE TCS.")
    ],
    start: Annotated[str, typer.Option(help="Inclusive start date (YYYY-MM-DD).")],
    end: Annotated[str | None, typer.Option(help="Inclusive end date (YYYY-MM-DD).")] = None,
) -> None:
    """Incrementally download and persist daily OHLCV data for NSE symbols."""
    settings = load_settings()
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end) if end else date.today()
    except ValueError as error:
        raise typer.BadParameter("Dates must use YYYY-MM-DD.") from error
    if settings.market.provider != "yahoo":
        raise typer.BadParameter(f"Unsupported configured provider: {settings.market.provider}")
    service = MarketDataService(
        YahooProvider(settings.market.exchange_suffix),
        PriceStore(
            settings.storage.data_directory,
            settings.storage.duckdb_path,
            settings.storage.parquet_compression,
        ),
    )
    for symbol in symbols:
        result = service.update(symbol.upper(), start_date, end_date)
        logger.info("Updated {} with {} rows", result.symbol, result.rows_written)
        typer.echo(f"{result.symbol}: {result.rows_written} rows")


@app.command()
def indicators(
    symbols: Annotated[list[str], typer.Argument(help="Stored NSE symbols to calculate.")],
    benchmark: Annotated[str | None, typer.Option(help="Stored benchmark symbol.")] = None,
) -> None:
    """Calculate and persist indicators from previously downloaded raw price data."""
    settings = load_settings()
    prices = PriceStore(
        settings.storage.data_directory,
        settings.storage.duckdb_path,
        settings.storage.parquet_compression,
    )
    service = IndicatorRefreshService(
        prices,
        IndicatorEngine(settings.indicators),
        IndicatorStore(settings.storage.data_directory, settings.storage.parquet_compression),
    )
    benchmark_symbol = benchmark or settings.market.benchmark_symbol
    for symbol in symbols:
        result = service.refresh(symbol.upper(), benchmark_symbol)
        typer.echo(f"{result.symbol}: {result.rows_processed} rows -> {result.output_path}")


@app.command()
def patterns(
    symbols: Annotated[list[str], typer.Argument(help="Symbols with processed indicator data.")],
) -> None:
    """Detect and persist the latest trend, structure, and price-action signals."""
    settings = load_settings()
    service = PatternAnalysisService(settings.storage.data_directory, TrendEngine(), SignalEngine())
    for symbol in symbols:
        result = service.analyse(symbol.upper())
        typer.echo(f"{result.symbol}: {result.trend}; {', '.join(result.signals) or 'no signals'}")


@app.command()
def score(
    symbols: Annotated[
        list[str], typer.Argument(help="Symbols with persisted indicator and pattern data.")
    ],
) -> None:
    """Score and rank symbols from the latest processed analysis."""
    settings = load_settings()
    service = ScoringService(settings.storage.data_directory, ScoreEngine(settings.scoring))
    for rank, result in enumerate(service.rank(symbols), start=1):
        typer.echo(f"{rank}. {result.symbol}: {result.total:.2f}")


@app.command()
def report(
    symbols: Annotated[list[str], typer.Argument(help="Symbols to include in ranked reports.")],
) -> None:
    """Export ranked opportunities as CSV, Parquet, and Excel."""
    settings = load_settings()
    scoring = ScoringService(settings.storage.data_directory, ScoreEngine(settings.scoring))
    paths = ReportService(settings.storage.data_directory, scoring).generate(symbols)
    for format_name, path in paths.items():
        typer.echo(f"{format_name}: {path}")


@app.command()
def dashboard() -> None:
    """Launch the interactive Streamlit dashboard."""
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/dashboard/main.py"], check=True)


@config_app.command("show")
def show_config(
    config: Annotated[
        Path | None, typer.Option("--config", "-c", help="Explicit YAML file.")
    ] = None,
) -> None:
    """Print validated runtime configuration as JSON."""
    settings = load_settings(config)
    logger.debug("Loaded configuration from CLI request")
    typer.echo(_settings_as_json(settings))


if __name__ == "__main__":
    app()
