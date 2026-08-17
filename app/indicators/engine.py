"""Vectorized technical indicators for daily OHLCV bars."""

from __future__ import annotations

import pandas as pd

from app.config.settings import IndicatorSettings


class IndicatorEngine:
    """Calculate reproducible daily technical features."""

    def __init__(self, settings: IndicatorSettings | None = None) -> None:
        self._settings = settings or IndicatorSettings()

    def calculate(self, prices: pd.DataFrame, benchmark: pd.Series | None = None) -> pd.DataFrame:
        """Return price bars enriched with trend, momentum, volatility, and volume features."""
        required = {"open", "high", "low", "close", "adj_close", "volume"}
        missing = required.difference(prices.columns)
        if missing:
            raise ValueError(f"Price frame is missing required columns: {sorted(missing)}")
        result = prices.copy().sort_index()
        close, high, low, volume = result["close"], result["high"], result["low"], result["volume"]
        for period in self._settings.sma_periods:
            result[f"sma_{period}"] = close.rolling(period, min_periods=period).mean()
        for period in self._settings.ema_periods:
            result[f"ema_{period}"] = close.ewm(
                span=period, adjust=False, min_periods=period
            ).mean()
        delta = close.diff()
        gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
        rsi = self._settings.rsi_period
        average_gain = gain.ewm(alpha=1 / rsi, adjust=False, min_periods=rsi).mean()
        average_loss = loss.ewm(alpha=1 / rsi, adjust=False, min_periods=rsi).mean()
        result[f"rsi_{rsi}"] = 100 - 100 / (
            1 + average_gain / average_loss.replace(0, float("nan"))
        )
        result["macd"] = (
            close.ewm(span=self._settings.macd_fast_period, adjust=False).mean()
            - close.ewm(span=self._settings.macd_slow_period, adjust=False).mean()
        )
        result["macd_signal"] = (
            result["macd"].ewm(span=self._settings.macd_signal_period, adjust=False).mean()
        )
        result["macd_histogram"] = result["macd"] - result["macd_signal"]
        atr_period = self._settings.atr_period
        previous_close = close.shift()
        true_range = pd.concat(
            [high - low, (high - previous_close).abs(), (low - previous_close).abs()], axis=1
        ).max(axis=1)
        result[f"atr_{atr_period}"] = true_range.ewm(
            alpha=1 / atr_period, adjust=False, min_periods=atr_period
        ).mean()
        up_move, down_move = high.diff(), -low.diff()
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
        adx_period = self._settings.adx_period
        plus_di = (
            100
            * plus_dm.ewm(alpha=1 / adx_period, adjust=False).mean()
            / result[f"atr_{atr_period}"]
        )
        minus_di = (
            100
            * minus_dm.ewm(alpha=1 / adx_period, adjust=False).mean()
            / result[f"atr_{atr_period}"]
        )
        result[f"adx_{adx_period}"] = (
            (100 * (plus_di - minus_di).abs() / (plus_di + minus_di))
            .ewm(alpha=1 / adx_period, adjust=False, min_periods=adx_period)
            .mean()
        )
        result["obv"] = (
            volume * close.diff().apply(lambda item: 1 if item > 0 else -1 if item < 0 else 0)
        ).cumsum()
        volume_period = self._settings.volume_average_period
        result[f"volume_sma_{volume_period}"] = volume.rolling(
            volume_period, min_periods=volume_period
        ).mean()
        result["volume_ratio"] = volume / result[f"volume_sma_{volume_period}"]
        bb_period = self._settings.bollinger_period
        middle, deviation = (
            close.rolling(bb_period, min_periods=bb_period).mean(),
            close.rolling(bb_period, min_periods=bb_period).std(),
        )
        result["bb_upper"], result["bb_lower"] = (
            middle + self._settings.bollinger_stddev * deviation,
            middle - self._settings.bollinger_stddev * deviation,
        )
        result["keltner_middle"] = close.ewm(
            span=self._settings.keltner_period, adjust=False
        ).mean()
        result["keltner_upper"] = (
            result["keltner_middle"]
            + self._settings.keltner_atr_multiplier * result[f"atr_{atr_period}"]
        )
        result["keltner_lower"] = (
            result["keltner_middle"]
            - self._settings.keltner_atr_multiplier * result[f"atr_{atr_period}"]
        )
        donchian_period = self._settings.donchian_period
        result["donchian_upper"], result["donchian_lower"] = (
            high.rolling(donchian_period, min_periods=donchian_period).max(),
            low.rolling(donchian_period, min_periods=donchian_period).min(),
        )
        result["rolling_high_20"], result["rolling_low_20"] = (
            result["donchian_upper"],
            result["donchian_lower"],
        )
        year_period = self._settings.fifty_two_week_period
        result["high_52w"], result["low_52w"] = (
            high.rolling(year_period, min_periods=year_period).max(),
            low.rolling(year_period, min_periods=year_period).min(),
        )
        if benchmark is not None:
            aligned = benchmark.reindex(result.index).ffill()
            result["relative_strength"] = (close / close.iloc[0]) / (aligned / aligned.iloc[0])
        return result
