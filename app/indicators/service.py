"""Application service for refreshing persisted indicator datasets."""

from dataclasses import dataclass
from pathlib import Path

from app.data.storage import PriceStore
from app.indicators.engine import IndicatorEngine
from app.indicators.storage import IndicatorStore


@dataclass(frozen=True)
class IndicatorRefreshResult:
    """Outcome of calculating one symbol's indicators."""

    symbol: str
    rows_processed: int
    output_path: Path


class IndicatorRefreshService:
    """Coordinate raw-price loading, feature calculation, and persistence."""

    def __init__(self, prices: PriceStore, engine: IndicatorEngine, output: IndicatorStore) -> None:
        self._prices = prices
        self._engine = engine
        self._output = output

    def refresh(self, symbol: str, benchmark_symbol: str | None = None) -> IndicatorRefreshResult:
        """Calculate and persist indicators for a stored symbol."""
        bars = self._prices.read(symbol)
        benchmark = self._prices.read(benchmark_symbol)["close"] if benchmark_symbol else None
        indicators = self._engine.calculate(bars, benchmark)
        path = self._output.write(symbol, indicators)
        return IndicatorRefreshResult(symbol, len(indicators), path)
