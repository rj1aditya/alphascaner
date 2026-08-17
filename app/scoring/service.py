"""Load persisted analysis and rank symbols."""

import json
from pathlib import Path

import pandas as pd

from app.scoring.engine import ScoreEngine, StockScore


class ScoringService:
    """Score processed indicator and pattern outputs."""

    def __init__(self, data_directory: Path, engine: ScoreEngine) -> None:
        self._indicator_root = data_directory / "processed" / "indicators"
        self._pattern_root = data_directory / "processed" / "patterns"
        self._engine = engine

    def rank(self, symbols: list[str]) -> list[StockScore]:
        """Score all requested symbols and return ranking order."""
        scores = [self._score_symbol(symbol.upper()) for symbol in symbols]
        return self._engine.rank(scores)

    def _score_symbol(self, symbol: str) -> StockScore:
        safe_symbol = symbol.replace("^", "index_")
        indicators = pd.read_parquet(self._indicator_root / f"{safe_symbol}.parquet")
        payload = json.loads((self._pattern_root / f"{safe_symbol}.json").read_text())
        signals = set(payload[0]["signals"].split(",")) if payload[0]["signals"] else set()
        return self._engine.score(symbol, indicators, signals)
