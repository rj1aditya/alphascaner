"""CSV, Parquet, and Excel ranked-report generation."""

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from app.scoring.service import ScoringService


class ReportService:
    """Build operator-ready opportunity reports from persisted analysis."""

    def __init__(self, data_directory: Path, scoring: ScoringService) -> None:
        self._data_directory = data_directory
        self._scoring = scoring

    def generate(self, symbols: list[str]) -> dict[str, Path]:
        """Write CSV, Parquet, and Excel ranked reports and return their paths."""
        rows = []
        for rank, score in enumerate(self._scoring.rank(symbols), start=1):
            frame = pd.read_parquet(
                self._data_directory / "processed" / "indicators" / f"{score.symbol}.parquet"
            )
            latest = frame.iloc[-1]
            rows.append(
                {
                    "rank": rank,
                    "symbol": score.symbol,
                    "price": latest["close"],
                    "sma_20": latest["sma_20"],
                    "sma_50": latest["sma_50"],
                    "sma_200": latest["sma_200"],
                    "rsi": latest["rsi_14"],
                    "atr": latest["atr_14"],
                    "volume_ratio": latest["volume_ratio"],
                    "score": score.total,
                }
            )
        report = pd.DataFrame(rows)
        root = self._data_directory / "reports"
        root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        csv_path, parquet_path, excel_path = (
            root / f"ranked_{stamp}.csv",
            root / f"ranked_{stamp}.parquet",
            root / f"ranked_{stamp}.xlsx",
        )
        report.to_csv(csv_path, index=False)
        report.to_parquet(parquet_path, index=False)
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            report.to_excel(writer, sheet_name="Ranked Opportunities", index=False)
            sheet = writer.book["Ranked Opportunities"]
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for column in sheet.columns:
                sheet.column_dimensions[column[0].column_letter].width = min(
                    max(len(str(cell.value or "")) for cell in column) + 2, 24
                )
        return {"csv": csv_path, "parquet": parquet_path, "excel": excel_path}
