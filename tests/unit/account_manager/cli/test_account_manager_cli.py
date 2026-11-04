from __future__ import annotations

import tomllib
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ai.backend.account_manager.cli.__main__ import main


class TestGenerateExampleConfigurationCommand:
    @pytest.fixture
    def generator_returning_an_example(self) -> Iterator[None]:
        with patch(
            "ai.backend.account_manager.config.generate_example_json",
            return_value={"key": "value"},
        ):
            yield

    @pytest.fixture
    def example_output_file(self, tmp_path: Path) -> Path:
        return tmp_path / "example.toml"

    @pytest.mark.usefixtures("generator_returning_an_example")
    def test_output_option_writes_the_example_to_the_file(self, example_output_file: Path) -> None:
        result = CliRunner().invoke(
            main, ["generate-example-configuration", "--output", str(example_output_file)]
        )

        assert result.exit_code == 0, result.output
        assert tomllib.loads(example_output_file.read_text()) == {"key": "value"}

    @pytest.mark.usefixtures("generator_returning_an_example")
    def test_without_output_option_writes_the_example_to_stdout(self) -> None:
        result = CliRunner().invoke(main, ["generate-example-configuration"])

        assert result.exit_code == 0, result.output
        assert tomllib.loads(result.stdout) == {"key": "value"}

    @pytest.mark.usefixtures("generator_returning_an_example")
    def test_log_level_option_is_accepted(self) -> None:
        result = CliRunner().invoke(
            main, ["--log-level", "DEBUG", "generate-example-configuration"]
        )

        assert result.exit_code == 0, result.output
