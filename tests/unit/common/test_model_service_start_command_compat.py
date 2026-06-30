from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.model_service_start_command_compat import (
    normalize_model_service_command_response,
    resolve_model_service_start_command,
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


class TestNormalizeModelServiceCommandResponse:
    @pytest.mark.parametrize(
        ("payload", "expected"),
        [
            pytest.param(
                {
                    "start_command": "python serve.py --name 'a b'",
                    "port": 8080,
                },
                {
                    "command": "python serve.py --name 'a b'",
                    "start_command": ["python", "serve.py", "--name", "a b"],
                    "port": 8080,
                },
                id="internal-string",
            ),
            pytest.param(
                {
                    "start_command": ["python", "serve.py"],
                    "port": 8080,
                },
                {
                    "command": "python serve.py",
                    "start_command": ["python", "serve.py"],
                    "port": 8080,
                },
                id="legacy-list",
            ),
            pytest.param(
                {
                    "start_command": "python 'unterminated",
                },
                {
                    "command": "python 'unterminated",
                    "start_command": ["python 'unterminated"],
                },
                id="unparseable-string",
            ),
        ],
    )
    def test_normalizes_response_fields(
        self,
        payload: dict[str, Any],
        expected: dict[str, Any],
    ) -> None:
        result = normalize_model_service_command_response(payload)

        assert result == expected
