"""Tests for v2 CLI ``.env`` auto-loading (BA-5794)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from ai.backend.client.cli.v2 import helpers


@pytest.fixture
def reset_dotenv_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[Path]:
    """Force ``_load_dotenv_once`` to re-run and isolate cwd / env vars."""
    monkeypatch.setattr(helpers, "_dotenv_loaded", False)
    monkeypatch.chdir(tmp_path)
    for key in (
        "BACKEND_ENDPOINT",
        "BACKEND_ENDPOINT_TYPE",
        "BACKEND_ACCESS_KEY",
        "BACKEND_SECRET_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    yield tmp_path


def test_load_dotenv_once_picks_up_cwd_dotenv(
    reset_dotenv_state: Path,
) -> None:
    (reset_dotenv_state / ".env").write_text(
        "BACKEND_ENDPOINT=https://from-dotenv.example\nBACKEND_ACCESS_KEY=ak-from-dotenv\n",
    )

    helpers._load_dotenv_once()

    assert os.environ["BACKEND_ENDPOINT"] == "https://from-dotenv.example"
    assert os.environ["BACKEND_ACCESS_KEY"] == "ak-from-dotenv"


def test_load_dotenv_once_overrides_existing_env(
    reset_dotenv_state: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BACKEND_ENDPOINT", "https://from-shell.example")
    (reset_dotenv_state / ".env").write_text(
        "BACKEND_ENDPOINT=https://from-dotenv.example\n",
    )

    helpers._load_dotenv_once()

    # ``override=True`` preserves v1 semantics — .env wins over pre-existing env.
    assert os.environ["BACKEND_ENDPOINT"] == "https://from-dotenv.example"


def test_load_v2_config_reads_dotenv(
    reset_dotenv_state: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Point CONFIG_FILE/CREDENTIALS_FILE to non-existent paths so only env applies.
    monkeypatch.setattr(helpers, "CONFIG_FILE", reset_dotenv_state / "missing-config.toml")
    monkeypatch.setattr(helpers, "CREDENTIALS_FILE", reset_dotenv_state / "missing-creds.toml")

    (reset_dotenv_state / ".env").write_text(
        "BACKEND_ENDPOINT=https://dotenv.example\n"
        "BACKEND_ACCESS_KEY=ak-x\n"
        "BACKEND_SECRET_KEY=sk-x\n",
    )

    cfg = helpers.load_v2_config()

    assert str(cfg.endpoint) == "https://dotenv.example"
    assert cfg.access_key == "ak-x"
    assert cfg.secret_key == "sk-x"


def test_load_dotenv_once_is_idempotent(
    reset_dotenv_state: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (reset_dotenv_state / ".env").write_text("BACKEND_ENDPOINT=https://first.example\n")
    helpers._load_dotenv_once()
    assert os.environ["BACKEND_ENDPOINT"] == "https://first.example"

    # Replace .env and call again — should be a no-op (already loaded).
    (reset_dotenv_state / ".env").write_text("BACKEND_ENDPOINT=https://second.example\n")
    helpers._load_dotenv_once()
    assert os.environ["BACKEND_ENDPOINT"] == "https://first.example"
