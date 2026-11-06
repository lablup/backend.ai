from __future__ import annotations

import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from ai.backend.appproxy.common.config import UnsupportedTypeError
from ai.backend.appproxy.coordinator.cli.__main__ import main as coordinator_cli
from ai.backend.appproxy.worker.cli.__main__ import main as worker_cli

_EXAMPLE_GENERATOR = "ai.backend.appproxy.common.config.generate_example_json"
_EXISTING_FILE_CONTENT = "existing = true\n"


@dataclass(frozen=True)
class _ExampleCommandCase:
    description: str
    cli: click.Group


class TestGenerateExampleConfigurationCommand:
    @pytest.fixture
    def generator_returning_an_example(self) -> Iterator[None]:
        with patch(_EXAMPLE_GENERATOR, return_value={"key": "value"}):
            yield

    @pytest.fixture
    def generator_raising_unsupported_type(self) -> Iterator[None]:
        with patch(_EXAMPLE_GENERATOR, side_effect=UnsupportedTypeError("unsupported")):
            yield

    @pytest.fixture
    def existing_output_file(self, tmp_path: Path) -> Path:
        output_file = tmp_path / "example.toml"
        output_file.write_text(_EXISTING_FILE_CONTENT)
        return output_file

    @pytest.mark.usefixtures("generator_returning_an_example")
    @pytest.mark.parametrize(
        "case",
        [
            _ExampleCommandCase(description="coordinator", cli=coordinator_cli),
            _ExampleCommandCase(description="worker", cli=worker_cli),
        ],
        ids=lambda case: case.description,
    )
    def test_output_option_writes_the_example_to_the_file(
        self, case: _ExampleCommandCase, existing_output_file: Path
    ) -> None:
        result = CliRunner().invoke(
            case.cli, ["generate-example-configuration", "--output", str(existing_output_file)]
        )

        assert result.exit_code == 0, result.output
        assert tomllib.loads(existing_output_file.read_text()) == {"key": "value"}

    @pytest.mark.usefixtures("generator_returning_an_example")
    @pytest.mark.parametrize(
        "case",
        [
            _ExampleCommandCase(description="coordinator", cli=coordinator_cli),
            _ExampleCommandCase(description="worker", cli=worker_cli),
        ],
        ids=lambda case: case.description,
    )
    def test_without_output_option_writes_the_example_to_stdout(
        self, case: _ExampleCommandCase
    ) -> None:
        result = CliRunner().invoke(case.cli, ["generate-example-configuration"])

        assert result.exit_code == 0, result.output
        assert tomllib.loads(result.stdout) == {"key": "value"}

    @pytest.mark.usefixtures("generator_raising_unsupported_type")
    @pytest.mark.parametrize(
        "case",
        [
            _ExampleCommandCase(description="coordinator", cli=coordinator_cli),
            _ExampleCommandCase(description="worker", cli=worker_cli),
        ],
        ids=lambda case: case.description,
    )
    def test_failed_generation_keeps_the_existing_output_file(
        self, case: _ExampleCommandCase, existing_output_file: Path
    ) -> None:
        result = CliRunner().invoke(
            case.cli, ["generate-example-configuration", "--output", str(existing_output_file)]
        )

        assert isinstance(result.exception, UnsupportedTypeError)
        assert existing_output_file.read_text() == _EXISTING_FILE_CONTENT
