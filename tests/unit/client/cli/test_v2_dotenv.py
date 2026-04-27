"""Tests for v2 CLI ``.env`` auto-loading (BA-5794)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from ai.backend.client.cli.v2 import helpers


@pytest.fixture
def dotenv_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[Path]:
    """Place a ``.env`` in an isolated cwd with no fallback config/credentials."""
    monkeypatch.chdir(tmp_path)
    for key in (
        "BACKEND_ENDPOINT",
        "BACKEND_ENDPOINT_TYPE",
        "BACKEND_ACCESS_KEY",
        "BACKEND_SECRET_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(helpers, "CONFIG_FILE", tmp_path / "missing-config.toml")
    monkeypatch.setattr(helpers, "CREDENTIALS_FILE", tmp_path / "missing-creds.toml")
    (tmp_path / ".env").write_text(
        "BACKEND_ENDPOINT=https://from-dotenv.example\nBACKEND_ACCESS_KEY=ak-from-dotenv\n",
    )
    yield tmp_path


def test_v2_cli_auto_loads_dotenv(
    runner: CliRunner,
    cli_entrypoint: Callable[[], click.Group],
    dotenv_environment: Path,
) -> None:
    """``./bai v2 ...`` auto-loads ``.env`` from cwd, matching v1 CLI behavior."""
    result = runner.invoke(cli_entrypoint, ["v2", "config", "show"])

    assert result.exit_code == 0, result.output
    assert "from-dotenv.example" in result.output
    assert "ak-from-dotenv" in result.output
