from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.model_service_start_command_compat import (
    resolve_model_service_start_command,
    to_legacy_start_command,
)


class TestNormalizeModelServiceCommandInput:
    @pytest.mark.parametrize(
        ("payload", "expected"),
        [
            pytest.param(
                {
                    "command": "python new.py",
                    "start_command": ["python", "old.py"],
                    "port": 8080,
                },
                {"start_command": "python new.py", "port": 8080},
                id="command-takes-precedence",
            ),
            pytest.param(
                {
                    "start-command": ["python", "serve.py", "--name", "a b"],
                    "port": 8080,
                },
                {"start_command": "python serve.py --name 'a b'", "port": 8080},
                id="hyphenated-start-command",
            ),
            pytest.param(
                {
                    "start-command": None,
                    "port": 8080,
                },
                {"start_command": None, "port": 8080},
                id="explicit-null",
            ),
        ],
    )
    def test_normalizes_mapping_input(
        self,
        payload: dict[str, Any],
        expected: dict[str, Any],
    ) -> None:
        result = resolve_model_service_start_command(payload)

        assert result == expected

    def test_non_mapping_input_passes_through(self) -> None:
        payload = ["not", "a", "service"]

        assert resolve_model_service_start_command(payload) is payload


class TestToLegacyStartCommand:
    @pytest.mark.parametrize(
        ("command", "expected"),
        [
            pytest.param(
                "python serve.py --name 'a b'",
                ["python", "serve.py", "--name", "a b"],
                id="internal-string",
            ),
            pytest.param(
                "python 'unterminated",
                ["python 'unterminated"],
                id="unparseable-string",
            ),
            pytest.param(
                None,
                None,
                id="none",
            ),
        ],
    )
    def test_derives_argv_form(
        self,
        command: str | None,
        expected: list[str] | None,
    ) -> None:
        assert to_legacy_start_command(command) == expected
