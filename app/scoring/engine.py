"""Configurable 0–100 opportunity scoring."""

from dataclasses import dataclass

import pandas as pd

from app.config.settings import ScoringSettings


@dataclass(frozen=True)
class StockScore:
    """A transparent score with its component contributions."""

    symbol: str
    total: float
    trend: float
    momentum: float
    pattern: float
    volume: float
    relative_strength: float
    risk: float


class ScoreEngine:
    """Score the latest enriched daily bar and detected pattern labels."""

    def __init__(self, settings: ScoringSettings | None = None) -> None:
        self._settings = settings or ScoringSettings()

    def score(self, symbol: str, indicators: pd.DataFrame, signals: set[str]) -> StockScore:
        """Return a bounded, explainable opportunity score."""
        latest = indicators.iloc[-1]
        trend = (
            self._settings.trend_weight
            if latest["close"] > latest["sma_50"] > latest["sma_200"]
            else 0
        )
        momentum = self._settings.momentum_weight * min(max(float(latest["rsi_14"]) / 70, 0), 1)
        pattern = self._settings.pattern_weight * min(len(signals) / 3, 1)
        volume = self._settings.volume_weight * min(float(latest["volume_ratio"]) / 2, 1)
        relative_strength = (
            self._settings.relative_strength_weight
            if latest.get("relative_strength", 0) >= 1
            else 0
        )
        risk = self._settings.risk_weight * max(
            0, 1 - float(latest["atr_14"]) / float(latest["close"]) / 0.05
        )
        total = min(100.0, trend + momentum + pattern + volume + relative_strength + risk)
        return StockScore(symbol, total, trend, momentum, pattern, volume, relative_strength, risk)

    def rank(self, scores: list[StockScore]) -> list[StockScore]:
        """Return scores ordered from highest to lowest, breaking ties by symbol."""
        return sorted(scores, key=lambda item: (-item.total, item.symbol))
