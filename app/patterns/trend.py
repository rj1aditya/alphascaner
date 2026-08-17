"""Deterministic daily trend and market-structure classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import pandas as pd


class TrendLabel(StrEnum):
    """Supported market trend states."""

    STRONG_UPTREND = "strong_uptrend"
    WEAK_UPTREND = "weak_uptrend"
    SIDEWAYS = "sideways"
    WEAK_DOWNTREND = "weak_downtrend"
    STRONG_DOWNTREND = "strong_downtrend"


class StructureLabel(StrEnum):
    """Recent swing-price market structure."""

    HIGHER_HIGH_HIGHER_LOW = "higher_high_higher_low"
    LOWER_HIGH_LOWER_LOW = "lower_high_lower_low"
    RANGE = "range"


@dataclass(frozen=True)
class TrendResult:
    """Trend and market-structure classification for the latest bar."""

    trend: TrendLabel
    structure: StructureLabel
    support: float
    resistance: float


class TrendEngine:
    """Classify trend using moving-average alignment, ADX, and recent price range."""

    def classify(self, indicators: pd.DataFrame) -> TrendResult:
        """Classify the most recent enriched daily bar."""
        required = {
            "close",
            "sma_20",
            "sma_50",
            "sma_200",
            "adx_14",
            "rolling_high_20",
            "rolling_low_20",
        }
        missing = required.difference(indicators.columns)
        if missing:
            raise ValueError(f"Indicators are missing required columns: {sorted(missing)}")
        latest = indicators.iloc[-1]
        adx = float(latest["adx_14"])
        bullish = latest["close"] > latest["sma_20"] > latest["sma_50"] > latest["sma_200"]
        bearish = latest["close"] < latest["sma_20"] < latest["sma_50"] < latest["sma_200"]
        if bullish:
            trend = TrendLabel.STRONG_UPTREND if adx >= 25 else TrendLabel.WEAK_UPTREND
        elif bearish:
            trend = TrendLabel.STRONG_DOWNTREND if adx >= 25 else TrendLabel.WEAK_DOWNTREND
        else:
            trend = TrendLabel.SIDEWAYS
        window = indicators.tail(20)
        structure = self._structure(window)
        return TrendResult(
            trend, structure, float(latest["rolling_low_20"]), float(latest["rolling_high_20"])
        )

    @staticmethod
    def _structure(window: pd.DataFrame) -> StructureLabel:
        """Classify recent price structure using first-versus-last halves."""
        midpoint = len(window) // 2
        first, last = window.iloc[:midpoint], window.iloc[midpoint:]
        if last["high"].max() > first["high"].max() and last["low"].min() > first["low"].min():
            return StructureLabel.HIGHER_HIGH_HIGHER_LOW
        if last["high"].max() < first["high"].max() and last["low"].min() < first["low"].min():
            return StructureLabel.LOWER_HIGH_LOWER_LOW
        return StructureLabel.RANGE
