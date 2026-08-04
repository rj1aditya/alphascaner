"""Tests for the public CLI surface."""

from app import __version__
from app.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_version_command() -> None:
    """The version command exposes the package version."""
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_config_show_command() -> None:
    """The configuration command returns JSON from default configuration."""
    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert '"provider": "yahoo"' in result.stdout
