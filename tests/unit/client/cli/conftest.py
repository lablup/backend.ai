from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from ai.backend.cli.loader import load_entry_points


@pytest.fixture
def isolated_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    world_readable_umask: None,
) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    for key in (
        "BACKEND_PROFILE",
        "BACKEND_ENDPOINT",
        "BACKEND_ENDPOINT_TYPE",
        "BACKEND_ACCESS_KEY",
        "BACKEND_SECRET_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    return tmp_path


@pytest.fixture(scope="module")
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(scope="module")
def cli_entrypoint() -> Callable[[], click.Group]:
    return load_entry_points(allowlist={"ai.backend.client.cli"})
