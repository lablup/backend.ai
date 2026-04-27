"""Tests for ``load_v2_config`` precedence (BA-5873).

Explicitly-saved files in ``~/.backend.ai/`` must win over ambient
``BACKEND_*`` env vars so a stray ``.env`` cannot silently swap a
logged-in user's saved credentials.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from ai.backend.client.cli.v2 import helpers


@pytest.fixture
def isolated_config_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[Path]:
    """Point the loader at a clean ~/.backend.ai/ replacement."""
    monkeypatch.setattr(helpers, "CONFIG_FILE", tmp_path / "config.toml")
    monkeypatch.setattr(helpers, "CREDENTIALS_FILE", tmp_path / "credentials.toml")
    monkeypatch.setattr(helpers, "COOKIE_FILE", tmp_path / "session" / "cookie.dat")
    for key in (
        "BACKEND_ENDPOINT",
        "BACKEND_ENDPOINT_TYPE",
        "BACKEND_ACCESS_KEY",
        "BACKEND_SECRET_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    yield tmp_path


def test_credentials_toml_wins_over_env_vars(
    isolated_config_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (isolated_config_dir / "credentials.toml").write_text(
        '[backend-ai]\naccess_key = "ak-from-file"\nsecret_key = "sk-from-file"\n',
    )
    monkeypatch.setenv("BACKEND_ACCESS_KEY", "ak-from-env")
    monkeypatch.setenv("BACKEND_SECRET_KEY", "sk-from-env")

    cfg = helpers.load_v2_config()

    assert cfg.access_key == "ak-from-file"
    assert cfg.secret_key == "sk-from-file"


def test_config_toml_wins_over_env_vars(
    isolated_config_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (isolated_config_dir / "config.toml").write_text(
        '[backend-ai]\nendpoint = "https://from-file.example"\nendpoint_type = "session"\n',
    )
    monkeypatch.setenv("BACKEND_ENDPOINT", "https://from-env.example")
    monkeypatch.setenv("BACKEND_ENDPOINT_TYPE", "api")

    cfg = helpers.load_v2_config()

    assert str(cfg.endpoint) == "https://from-file.example"
    assert cfg.endpoint_type == "session"


def test_env_vars_used_when_files_absent(
    isolated_config_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BACKEND_ENDPOINT", "https://from-env.example")
    monkeypatch.setenv("BACKEND_ACCESS_KEY", "ak-from-env")
    monkeypatch.setenv("BACKEND_SECRET_KEY", "sk-from-env")

    cfg = helpers.load_v2_config()

    assert str(cfg.endpoint) == "https://from-env.example"
    assert cfg.access_key == "ak-from-env"
    assert cfg.secret_key == "sk-from-env"


def test_partial_credentials_file_falls_back_to_env_per_field(
    isolated_config_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the file provides only one of access/secret, env supplies the other."""
    (isolated_config_dir / "credentials.toml").write_text(
        '[backend-ai]\naccess_key = "ak-from-file"\n',
    )
    monkeypatch.setenv("BACKEND_ACCESS_KEY", "ak-from-env")
    monkeypatch.setenv("BACKEND_SECRET_KEY", "sk-from-env")

    cfg = helpers.load_v2_config()

    assert cfg.access_key == "ak-from-file"
    assert cfg.secret_key == "sk-from-env"
