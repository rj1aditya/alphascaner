"""Rule-based consolidation, breakout, and moving-average crossover signals."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import pandas as pd


class SignalLabel(StrEnum):
    """Price-action and crossover events supported by the initial pattern engine."""

    CONSOLIDATION = "consolidation"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    GOLDEN_CROSS = "golden_cross"
    DEATH_CROSS = "death_cross"
    INSIDE_BAR = "inside_bar"
    NR7 = "nr7"
    FIFTY_TWO_WEEK_BREAKOUT = "fifty_two_week_breakout"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    RECTANGLE = "rectangle"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRICAL_TRIANGLE = "symmetrical_triangle"
    VCP = "volatility_contraction_pattern"
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    BULLISH_PENNANT = "bullish_pennant"
    BEARISH_PENNANT = "bearish_pennant"
    CUP_AND_HANDLE = "cup_and_handle"
    TREND_CONTINUATION = "trend_continuation"
    TREND_REVERSAL = "trend_reversal"


@dataclass(frozen=True)
class PatternSignal:
    """A detected signal with its confirmation level."""

    label: SignalLabel
    confidence: float


class SignalEngine:
    """Detect price-action and moving-average signals from enriched daily bars."""

    def detect(self, indicators: pd.DataFrame) -> list[PatternSignal]:
        """Return every confirmed signal at the latest daily bar."""
        if len(indicators) < 21:
            return []
        required = {"close", "high", "low", "volume_ratio", "atr_14", "sma_50", "sma_200"}
        missing = required.difference(indicators.columns)
        if missing:
            raise ValueError(f"Indicators are missing required columns: {sorted(missing)}")
        latest, previous = indicators.iloc[-1], indicators.iloc[-2]
        range_high = indicators["high"].iloc[-21:-1].max()
        range_low = indicators["low"].iloc[-21:-1].min()
        range_width = (range_high - range_low) / range_low
        signals: list[PatternSignal] = []
        if range_width <= 0.08 and latest["atr_14"] / latest["close"] <= 0.03:
            signals.append(PatternSignal(SignalLabel.CONSOLIDATION, 0.7))
        if latest["close"] > range_high and latest["volume_ratio"] >= 1.5:
            signals.append(PatternSignal(SignalLabel.BREAKOUT, 0.9))
        if latest["close"] < range_low and latest["volume_ratio"] >= 1.5:
            signals.append(PatternSignal(SignalLabel.BREAKDOWN, 0.9))
        if previous["sma_50"] <= previous["sma_200"] and latest["sma_50"] > latest["sma_200"]:
            signals.append(PatternSignal(SignalLabel.GOLDEN_CROSS, 0.8))
        if previous["sma_50"] >= previous["sma_200"] and latest["sma_50"] < latest["sma_200"]:
            signals.append(PatternSignal(SignalLabel.DEATH_CROSS, 0.8))
        if latest["high"] <= previous["high"] and latest["low"] >= previous["low"]:
            signals.append(PatternSignal(SignalLabel.INSIDE_BAR, 0.7))
        recent_ranges = (indicators["high"] - indicators["low"]).tail(7)
        if len(recent_ranges) == 7 and recent_ranges.iloc[-1] == recent_ranges.min():
            signals.append(PatternSignal(SignalLabel.NR7, 0.7))
        if "high_52w" in indicators and latest["close"] >= latest["high_52w"]:
            signals.append(PatternSignal(SignalLabel.FIFTY_TWO_WEEK_BREAKOUT, 0.9))
        if len(indicators) >= 40:
            closes = indicators["close"].tail(40)
            midpoint = len(closes) // 2
            first_peak, second_peak = closes.iloc[:midpoint].max(), closes.iloc[midpoint:].max()
            first_trough, second_trough = closes.iloc[:midpoint].min(), closes.iloc[midpoint:].min()
            if abs(first_peak - second_peak) / max(first_peak, 1) <= 0.03:
                signals.append(PatternSignal(SignalLabel.DOUBLE_TOP, 0.6))
            if abs(first_trough - second_trough) / max(first_trough, 1) <= 0.03:
                signals.append(PatternSignal(SignalLabel.DOUBLE_BOTTOM, 0.6))
        if len(indicators) >= 20:
            window = indicators.tail(20)
            highs, lows = window["high"], window["low"]
            high_slope = highs.iloc[-10:].mean() - highs.iloc[:10].mean()
            low_slope = lows.iloc[-10:].mean() - lows.iloc[:10].mean()
            width_start = highs.iloc[:5].max() - lows.iloc[:5].min()
            width_end = highs.iloc[-5:].max() - lows.iloc[-5:].min()
            if abs(high_slope) / latest["close"] < 0.01 and abs(low_slope) / latest["close"] < 0.01:
                signals.append(PatternSignal(SignalLabel.RECTANGLE, 0.6))
            elif abs(high_slope) / latest["close"] < 0.01 and low_slope > 0:
                signals.append(PatternSignal(SignalLabel.ASCENDING_TRIANGLE, 0.6))
            elif high_slope < 0 and abs(low_slope) / latest["close"] < 0.01:
                signals.append(PatternSignal(SignalLabel.DESCENDING_TRIANGLE, 0.6))
            elif high_slope < 0 and low_slope > 0:
                signals.append(PatternSignal(SignalLabel.SYMMETRICAL_TRIANGLE, 0.6))
            if (
                width_end < width_start * 0.7
                and window["volume"].iloc[-5:].mean() < window["volume"].iloc[:5].mean()
            ):
                signals.append(PatternSignal(SignalLabel.VCP, 0.65))
            change = window["close"].iloc[-1] / window["close"].iloc[0] - 1
            if (
                change > 0.05
                and low_slope < 0
                and latest["close"] >= window["close"].iloc[-5:].max()
            ):
                signals.append(PatternSignal(SignalLabel.BULL_FLAG, 0.55))
            if (
                change < -0.05
                and high_slope > 0
                and latest["close"] <= window["close"].iloc[-5:].min()
            ):
                signals.append(PatternSignal(SignalLabel.BEAR_FLAG, 0.55))
            if width_end < width_start * 0.5:
                signals.append(
                    PatternSignal(
                        SignalLabel.BULLISH_PENNANT if change > 0 else SignalLabel.BEARISH_PENNANT,
                        0.5,
                    )
                )
            if (
                len(indicators) >= 60
                and window["close"].iloc[-1] > window["close"].iloc[:10].mean()
            ):
                signals.append(PatternSignal(SignalLabel.CUP_AND_HANDLE, 0.4))
            if latest["close"] > latest["sma_50"] and latest["sma_50"] > latest["sma_200"]:
                signals.append(PatternSignal(SignalLabel.TREND_CONTINUATION, 0.6))
            elif latest["close"] > latest["sma_50"] and previous["sma_50"] <= previous["sma_200"]:
                signals.append(PatternSignal(SignalLabel.TREND_REVERSAL, 0.55))
        return signals
