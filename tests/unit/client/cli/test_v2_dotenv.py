"""Tests for v2 CLI ``.env`` auto-loading (BA-5794)."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

import click
import pytest
from click.testing import CliRunner

from ai.backend.client.cli.v2 import helpers, v2


@dataclass(frozen=True)
class _DotenvPrecedenceCase:
    inherited_environ: dict[str, str]
    expected_endpoint: str


@pytest.fixture
def dotenv_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[Path]:
    """Place a ``.env`` in an isolated cwd with no fallback config/credentials."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".env").write_text(
        "BACKEND_ENDPOINT=https://from-dotenv.example\nBACKEND_ACCESS_KEY=ak-from-dotenv\n",
    )
    # ``load_dotenv`` writes straight into ``os.environ``, which monkeypatch does not undo.
    with mock.patch.dict(os.environ):
        for key in (
            "BACKEND_ENDPOINT",
            "BACKEND_ENDPOINT_TYPE",
            "BACKEND_ACCESS_KEY",
            "BACKEND_SECRET_KEY",
            helpers.PROFILE_ENV,
        ):
            os.environ.pop(key, None)
        yield tmp_path


@pytest.fixture
def dotenv_with_inherited_environ(
    case: _DotenvPrecedenceCase,
    dotenv_environment: Path,
) -> None:
    os.environ.update(case.inherited_environ)


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


@pytest.mark.parametrize(
    "case",
    [
        _DotenvPrecedenceCase(
            inherited_environ={"BACKEND_ENDPOINT": "https://from-environment.example"},
            expected_endpoint="https://from-environment.example",
        ),
        _DotenvPrecedenceCase(
            inherited_environ={},
            expected_endpoint="https://from-dotenv.example",
        ),
    ],
    ids=lambda case: case.expected_endpoint,
)
@pytest.mark.usefixtures("dotenv_with_inherited_environ")
def test_cli_entrypoint_prefers_environment_over_dotenv(
    runner: CliRunner,
    cli_entrypoint: Callable[[], click.Group],
    case: _DotenvPrecedenceCase,
) -> None:
    result = runner.invoke(cli_entrypoint, ["v2", "config", "get", "endpoint"])

    assert result.output.strip() == case.expected_endpoint


@pytest.mark.parametrize(
    "case",
    [
        _DotenvPrecedenceCase(
            inherited_environ={"BACKEND_ENDPOINT": "https://from-environment.example"},
            expected_endpoint="https://from-environment.example",
        ),
        _DotenvPrecedenceCase(
            inherited_environ={},
            expected_endpoint="https://from-dotenv.example",
        ),
    ],
    ids=lambda case: case.expected_endpoint,
)
@pytest.mark.usefixtures("dotenv_with_inherited_environ")
def test_v2_group_prefers_environment_over_dotenv(
    runner: CliRunner,
    case: _DotenvPrecedenceCase,
) -> None:
    result = runner.invoke(v2, ["config", "get", "endpoint"])

    assert result.output.strip() == case.expected_endpoint
