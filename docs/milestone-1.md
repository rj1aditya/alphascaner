# Milestone 1: Foundation

## Delivered

- An installable Python 3.12+ package and stable `alphascanner` CLI entry point.
- Immutable, validated Pydantic YAML configuration.
- Explicit configuration paths and an `ALPHASCANNER_CONFIG` environment override.
- Centralised Loguru console logging and daily rotating compressed logs retained for 30 days.
- Pytest coverage enforcement, Ruff linting, and strict MyPy checking.
- A repository layout that isolates future application layers.

## Layer boundaries

`config` owns validated operational settings and `core` owns cross-cutting infrastructure. Data
providers and domain engines will depend inward on these contracts, never on CLI or dashboard
adapters. The CLI initialises infrastructure then invokes application use cases.

## Next milestone

Milestone 2 will add the provider abstraction, a Yahoo Finance implementation, Parquet prices,
DuckDB metadata, and incremental update behaviour.
