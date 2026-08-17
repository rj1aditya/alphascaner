"""Typed runtime configuration for AlphaScanner."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

DEFAULT_CONFIG_PATH = Path("config/config.yaml")
EXAMPLE_CONFIG_PATH = Path("config/config.example.yaml")


class ConfigurationError(RuntimeError):
    """Raised when the AlphaScanner configuration cannot be loaded safely."""


class ApplicationSettings(BaseModel):
    """Application-wide operational settings."""

    model_config = ConfigDict(frozen=True)
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_directory: Path = Path("logs")
    timezone: str = "Asia/Kolkata"


class StorageSettings(BaseModel):
    """Local persistence settings."""

    model_config = ConfigDict(frozen=True)
    data_directory: Path = Path("data")
    duckdb_path: Path = Path("data/database.duckdb")
    parquet_compression: Literal["snappy", "gzip", "brotli", "lz4", "zstd", "none"] = "zstd"


class MarketSettings(BaseModel):
    """Market data conventions used throughout the application."""

    model_config = ConfigDict(frozen=True)
    provider: str = Field(default="yahoo", min_length=1)
    benchmark_symbol: str = Field(default="^NSEI", min_length=1)
    exchange_suffix: str = ".NS"


class IndicatorSettings(BaseModel):
    """Validated parameters used by the technical-indicator engine."""

    model_config = ConfigDict(frozen=True)
    sma_periods: tuple[int, ...] = (20, 50, 100, 150, 200)
    ema_periods: tuple[int, ...] = (20, 50, 100, 150, 200)
    rsi_period: int = Field(default=14, ge=2)
    atr_period: int = Field(default=14, ge=2)
    adx_period: int = Field(default=14, ge=2)
    macd_fast_period: int = Field(default=12, ge=2)
    macd_slow_period: int = Field(default=26, ge=2)
    macd_signal_period: int = Field(default=9, ge=2)
    bollinger_period: int = Field(default=20, ge=2)
    bollinger_stddev: float = Field(default=2.0, gt=0)
    keltner_period: int = Field(default=20, ge=2)
    keltner_atr_multiplier: float = Field(default=2.0, gt=0)
    donchian_period: int = Field(default=20, ge=2)
    volume_average_period: int = Field(default=20, ge=2)
    rolling_high_low_period: int = Field(default=20, ge=2)
    fifty_two_week_period: int = Field(default=252, ge=2)


class ScoringSettings(BaseModel):
    """Weights for the opportunity-ranking model; they must total 100."""

    model_config = ConfigDict(frozen=True)
    trend_weight: float = Field(default=25, ge=0)
    momentum_weight: float = Field(default=15, ge=0)
    pattern_weight: float = Field(default=25, ge=0)
    volume_weight: float = Field(default=15, ge=0)
    relative_strength_weight: float = Field(default=10, ge=0)
    risk_weight: float = Field(default=10, ge=0)


class Settings(BaseModel):
    """Validated aggregate application configuration."""

    model_config = ConfigDict(frozen=True)
    application: ApplicationSettings = ApplicationSettings()
    storage: StorageSettings = StorageSettings()
    market: MarketSettings = MarketSettings()
    indicators: IndicatorSettings = IndicatorSettings()
    scoring: ScoringSettings = ScoringSettings()


def _resolve_config_path(config_path: Path | None) -> Path:
    """Resolve configuration path, allowing an environment override."""
    if config_path is not None:
        return config_path
    configured_path = os.getenv("ALPHASCANNER_CONFIG")
    return Path(configured_path) if configured_path else DEFAULT_CONFIG_PATH


def _read_yaml(path: Path) -> dict[str, object]:
    """Read a YAML mapping from *path* and provide actionable errors."""
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ConfigurationError(f"Unable to read configuration file: {path}") from error
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid YAML in configuration file: {path}") from error
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ConfigurationError(f"Configuration root must be a mapping: {path}")
    return parsed


@lru_cache(maxsize=4)
def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from YAML, falling back to the supplied example configuration."""
    selected_path = _resolve_config_path(config_path)
    source_path = selected_path if selected_path.exists() else EXAMPLE_CONFIG_PATH
    try:
        return Settings.model_validate(_read_yaml(source_path))
    except ValidationError as error:
        raise ConfigurationError(f"Invalid configuration in {source_path}: {error}") from error
