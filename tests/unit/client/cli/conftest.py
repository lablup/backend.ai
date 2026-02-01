from __future__ import annotations

from collections.abc import Callable

import click
import pytest
from click.testing import CliRunner

from ai.backend.cli.loader import load_entry_points


@pytest.fixture(scope="module")
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(scope="module")
def cli_entrypoint() -> Callable[[], click.Group]:
    return load_entry_points(allowlist={"ai.backend.client.cli"})
