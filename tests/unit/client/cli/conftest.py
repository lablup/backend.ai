import pytest
from click.testing import CliRunner

from ai.backend.cli.loader import load_entry_points


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


@pytest.fixture(scope="module")
def cli_entrypoint():
    return load_entry_points(allowlist={"ai.backend.client.cli"})
