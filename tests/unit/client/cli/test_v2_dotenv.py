"""Tests for v2 CLI ``.env`` auto-loading (BA-5794)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from ai.backend.client.cli.v2 import helpers


@pytest.fixture
def isolated_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[Path]:
    """Isolate cwd and clear BACKEND_* env vars for each test."""
    monkeypatch.chdir(tmp_path)
    for key in (
        "BACKEND_ENDPOINT",
        "BACKEND_ENDPOINT_TYPE",
        "BACKEND_ACCESS_KEY",
        "BACKEND_SECRET_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    yield tmp_path


def test_load_cwd_dotenv_picks_up_cwd_dotenv(
    isolated_env: Path,
) -> None:
    (isolated_env / ".env").write_text(
        "BACKEND_ENDPOINT=https://from-dotenv.example\nBACKEND_ACCESS_KEY=ak-from-dotenv\n",
    )

    helpers._load_cwd_dotenv()

    assert os.environ["BACKEND_ENDPOINT"] == "https://from-dotenv.example"
    assert os.environ["BACKEND_ACCESS_KEY"] == "ak-from-dotenv"


def test_load_cwd_dotenv_overrides_existing_env(
    isolated_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BACKEND_ENDPOINT", "https://from-shell.example")
    (isolated_env / ".env").write_text(
        "BACKEND_ENDPOINT=https://from-dotenv.example\n",
    )

    helpers._load_cwd_dotenv()

    # ``override=True`` preserves v1 semantics — .env wins over pre-existing env.
    assert os.environ["BACKEND_ENDPOINT"] == "https://from-dotenv.example"


def test_load_v2_config_reads_dotenv(
    isolated_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Point CONFIG_FILE/CREDENTIALS_FILE to non-existent paths so only env applies.
    monkeypatch.setattr(helpers, "CONFIG_FILE", isolated_env / "missing-config.toml")
    monkeypatch.setattr(helpers, "CREDENTIALS_FILE", isolated_env / "missing-creds.toml")

    (isolated_env / ".env").write_text(
        "BACKEND_ENDPOINT=https://dotenv.example\nBACKEND_ACCESS_KEY=ak-x\nBACKEND_SECRET_KEY=sk-x\n",
    )

    cfg = helpers.load_v2_config()

    assert str(cfg.endpoint) == "https://dotenv.example"
    assert cfg.access_key == "ak-x"
    assert cfg.secret_key == "sk-x"
