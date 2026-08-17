# AlphaScanner

Professional Quantitative Positional Trading Scanner for NSE.

AlphaScanner is being delivered through production-ready milestones. Milestone 1 establishes the package foundation: configuration validation, structured file logging, a Typer CLI, automated tests, and consistent quality tooling.

## Quick start

Requires Python 3.12 or newer.

```powershell
cd alphascanner
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
alphascanner version
alphascanner config show
```

Copy `config/config.example.yaml` to `config/config.yaml` to customise runtime settings. The application also honours the `ALPHASCANNER_CONFIG` environment variable as a path to a YAML file.

## Development

```powershell
ruff check .
mypy app
pytest
```

See [Milestone 1](docs/milestone-1.md) for architecture and the delivery roadmap.
