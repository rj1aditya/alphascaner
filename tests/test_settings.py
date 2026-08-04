"""Tests for configuration loading."""

from pathlib import Path

import pytest
from app.config.settings import ConfigurationError, load_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """Ensure tests do not receive a cached settings instance."""
    load_settings.cache_clear()


def test_load_settings_uses_explicit_yaml(tmp_path: Path) -> None:
    """Explicit YAML values are validated and exposed."""
    config_path = tmp_path / "scanner.yaml"
    config_path.write_text("application:\n  environment: test\nmarket:\n  provider: fixture\n")

    settings = load_settings(config_path)

    assert settings.application.environment == "test"
    assert settings.market.provider == "fixture"


def test_load_settings_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    """Configuration documents require a mapping root."""
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("- not\n- a mapping\n")

    with pytest.raises(ConfigurationError, match="root must be a mapping"):
        load_settings(config_path)
