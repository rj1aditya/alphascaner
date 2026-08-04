"""Central logging configuration."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from app.config.settings import ApplicationSettings


def configure_logging(settings: ApplicationSettings) -> None:
    """Configure console and rotating file logging."""
    settings.log_directory.mkdir(parents=True, exist_ok=True)
    log_path: Path = settings.log_directory / "alphascanner_{time:YYYY-MM-DD}.log"
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level, format="{time} | {level:<8} | {message}")
    logger.add(
        log_path,
        level=settings.log_level,
        rotation="00:00",
        retention="30 days",
        compression="zip",
        enqueue=True,
        format="{time} | {level:<8} | {name}:{function}:{line} | {message}",
    )
