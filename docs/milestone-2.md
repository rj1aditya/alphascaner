# Milestone 2: Data Engine

## Delivered

The data layer separates the `MarketDataProvider` port from provider adapters. `YahooProvider`
normalizes Yahoo Finance daily OHLCV output; `PriceStore` stores each instrument as Parquet and
maintains a DuckDB catalog. `MarketDataService` implements incremental refreshes, beginning after
the latest stored bar and deduplicating by date during writes.

## Usage

```bash
alphascanner update RELIANCE TCS --start 2024-01-01
```

Yahoo Finance uses `.NS` for NSE equities automatically; index tickers such as `^NSEI` are
preserved. Later providers implement the same `MarketDataProvider` port without changing the
storage or CLI use case.

## Next milestone

Milestone 3 will build the indicator engine over these persisted daily bars.
