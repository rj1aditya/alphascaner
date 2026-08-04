"""Parquet price storage with a DuckDB metadata catalog."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal, cast

import duckdb
import pandas as pd


class PriceStore:
    """Persist normalized price bars and their update metadata."""

    def __init__(self, data_directory: Path, database_path: Path, compression: str) -> None:
        self._root = data_directory / "raw" / "daily"
        self._database_path = database_path
        self._compression = compression
        self._root.mkdir(parents=True, exist_ok=True)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise_catalog()

    def latest_date(self, symbol: str) -> date | None:
        """Return the latest stored trading date for a symbol."""
        with duckdb.connect(str(self._database_path), read_only=True) as connection:
            row = connection.execute(
                "SELECT max_date FROM price_catalog WHERE symbol = ?", [symbol]
            ).fetchone()
        return row[0] if row is not None else None

    def upsert(self, symbol: str, provider: str, bars: pd.DataFrame) -> int:
        """Merge new bars with existing data, deduplicate by date, and update catalog."""
        if bars.empty:
            return 0
        path = self._path(symbol)
        existing = pd.read_parquet(path) if path.exists() else pd.DataFrame()
        combined = pd.concat([existing, bars]).sort_index()
        combined = combined[~combined.index.duplicated(keep="last")]
        compression = cast(
            Literal["snappy", "gzip", "brotli", "lz4", "zstd"] | None,
            None if self._compression == "none" else self._compression,
        )
        combined.to_parquet(path, compression=compression)
        now = datetime.now(UTC)
        with duckdb.connect(str(self._database_path)) as connection:
            connection.execute(
                """INSERT INTO price_catalog AS catalog
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    provider = excluded.provider,
                    min_date = excluded.min_date,
                    max_date = excluded.max_date,
                    row_count = excluded.row_count,
                    updated_at = excluded.updated_at""",
                [
                    symbol,
                    provider,
                    combined.index.min().date(),
                    combined.index.max().date(),
                    len(combined),
                    now,
                ],
            )
        return len(bars)

    def read(self, symbol: str) -> pd.DataFrame:
        """Read all persisted bars for a symbol."""
        return pd.read_parquet(self._path(symbol))

    def _initialise_catalog(self) -> None:
        with duckdb.connect(str(self._database_path)) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS price_catalog (
                symbol VARCHAR PRIMARY KEY, provider VARCHAR NOT NULL, min_date DATE NOT NULL,
                max_date DATE NOT NULL, row_count BIGINT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL)"""
            )

    def _path(self, symbol: str) -> Path:
        safe_symbol = symbol.replace("^", "index_").replace("/", "_")
        return self._root / f"{safe_symbol}.parquet"
