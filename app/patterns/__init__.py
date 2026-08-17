"""Trend, market-structure, and chart-pattern detection."""

from app.patterns.signals import SignalEngine
from app.patterns.trend import TrendEngine, TrendResult

__all__ = ["SignalEngine", "TrendEngine", "TrendResult"]
