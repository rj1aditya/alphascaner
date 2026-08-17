"""Persistence for derived indicator datasets."""

from pathlib import Path
from typing import Literal, cast

import pandas as pd


class IndicatorStore:
    """Persist per-symbol calculated features independently from raw prices."""

    def __init__(self, data_directory: Path, compression: str) -> None:
        self._root = data_directory / "processed" / "indicators"
        self._compression = compression
        self._root.mkdir(parents=True, exist_ok=True)

    def write(self, symbol: str, indicators: pd.DataFrame) -> Path:
        """Write an indicator frame and return its deterministic storage path."""
        path = self._root / f"{symbol.replace('^', 'index_')}.parquet"
        temporary_path = path.with_suffix(".tmp.parquet")
        compression = cast(
            Literal["snappy", "gzip", "brotli", "lz4", "zstd"] | None,
            None if self._compression == "none" else self._compression,
        )
        indicators.to_parquet(temporary_path, compression=compression)
        temporary_path.replace(path)
        return path
