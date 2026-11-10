from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ai.backend.account_manager.cli.__main__ import main


class TestAccountManagerCLIGroup:
    @pytest.fixture
    def generator_returning_an_example(self) -> Iterator[None]:
        with patch(
            "ai.backend.account_manager.config.generate_example_json",
            return_value={"key": "value"},
        ):
            yield

    @pytest.mark.usefixtures("generator_returning_an_example")
    def test_log_level_option_is_accepted(self) -> None:
        result = CliRunner().invoke(
            main, ["--log-level", "DEBUG", "generate-example-configuration"]
        )

        assert result.exit_code == 0, result.output
