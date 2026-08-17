"""Persisted indicator analysis use case."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.patterns.signals import SignalEngine
from app.patterns.trend import TrendEngine


@dataclass(frozen=True)
class PatternAnalysis:
    """Latest trend and signal analysis for one symbol."""

    symbol: str
    trend: str
    structure: str
    signals: tuple[str, ...]
    output_path: Path


class PatternAnalysisService:
    """Read processed indicators and persist the latest pattern analysis."""

    def __init__(self, data_directory: Path, trends: TrendEngine, signals: SignalEngine) -> None:
        self._indicator_root = data_directory / "processed" / "indicators"
        self._output_root = data_directory / "processed" / "patterns"
        self._trends = trends
        self._signals = signals
        self._output_root.mkdir(parents=True, exist_ok=True)

    def analyse(self, symbol: str) -> PatternAnalysis:
        """Analyse one persisted indicator dataset."""
        safe_symbol = symbol.replace("^", "index_")
        indicators = pd.read_parquet(self._indicator_root / f"{safe_symbol}.parquet")
        trend = self._trends.classify(indicators)
        signals = tuple(signal.label.value for signal in self._signals.detect(indicators))
        output_path = self._output_root / f"{safe_symbol}.json"
        pd.DataFrame(
            [
                {
                    "symbol": symbol,
                    "trend": trend.trend.value,
                    "structure": trend.structure.value,
                    "support": trend.support,
                    "resistance": trend.resistance,
                    "signals": ",".join(signals),
                }
            ]
        ).to_json(output_path, orient="records")
        return PatternAnalysis(
            symbol, trend.trend.value, trend.structure.value, signals, output_path
        )
