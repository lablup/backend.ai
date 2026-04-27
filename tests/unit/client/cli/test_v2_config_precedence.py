"""Tests for ``load_v2_config`` precedence (BA-5873).

Explicitly-saved files in ``~/.backend.ai/`` must win over ambient
``BACKEND_*`` env vars so a stray ``.env`` cannot silently swap a
logged-in user's saved credentials.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.client.cli.v2 import helpers


def test_saved_files_win_over_env_vars(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(helpers, "CONFIG_FILE", tmp_path / "config.toml")
    monkeypatch.setattr(helpers, "CREDENTIALS_FILE", tmp_path / "credentials.toml")
    monkeypatch.setattr(helpers, "COOKIE_FILE", tmp_path / "session" / "cookie.dat")
    (tmp_path / "config.toml").write_text(
        '[backend-ai]\nendpoint = "https://from-file.example"\nendpoint_type = "session"\n',
    )
    (tmp_path / "credentials.toml").write_text(
        '[backend-ai]\naccess_key = "ak-from-file"\nsecret_key = "sk-from-file"\n',
    )
    monkeypatch.setenv("BACKEND_ENDPOINT", "https://from-env.example")
    monkeypatch.setenv("BACKEND_ENDPOINT_TYPE", "api")
    monkeypatch.setenv("BACKEND_ACCESS_KEY", "ak-from-env")
    monkeypatch.setenv("BACKEND_SECRET_KEY", "sk-from-env")

    cfg = helpers.load_v2_config()

    assert str(cfg.endpoint) == "https://from-file.example"
    assert cfg.endpoint_type == "session"
    assert cfg.access_key == "ak-from-file"
    assert cfg.secret_key == "sk-from-file"
