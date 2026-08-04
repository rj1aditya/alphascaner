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


class Settings(BaseModel):
    """Validated aggregate application configuration."""

    model_config = ConfigDict(frozen=True)
    application: ApplicationSettings = ApplicationSettings()
    storage: StorageSettings = StorageSettings()
    market: MarketSettings = MarketSettings()


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
