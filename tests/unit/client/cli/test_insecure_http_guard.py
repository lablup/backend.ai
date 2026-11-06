from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import override
from unittest.mock import MagicMock

import click
import pytest
from click.testing import CliRunner
from yarl import URL

from ai.backend.client.cli.insecure_http_guard import (
    SecretSendingCommand,
    reject_insecure_secret_endpoints,
)


class _CommandReadingInsecureEndpoint(SecretSendingCommand):
    @override
    def _load_endpoints(self) -> Iterable[URL]:
        return [URL("http://backend.example")]


@dataclass(frozen=True)
class _CommandAtInsecureEndpoint:
    command: click.Command
    body: MagicMock


@pytest.fixture
def command_at_insecure_endpoint() -> _CommandAtInsecureEndpoint:
    body = MagicMock()
    return _CommandAtInsecureEndpoint(
        command=_CommandReadingInsecureEndpoint(name="command", callback=body),
        body=body,
    )


class TestSecretSendingCommand:
    def test_refuses_without_the_allow_option(
        self,
        command_at_insecure_endpoint: _CommandAtInsecureEndpoint,
    ) -> None:
        CliRunner().invoke(command_at_insecure_endpoint.command, [])

        command_at_insecure_endpoint.body.assert_not_called()

    def test_runs_the_body_with_the_allow_option(
        self,
        command_at_insecure_endpoint: _CommandAtInsecureEndpoint,
    ) -> None:
        CliRunner().invoke(command_at_insecure_endpoint.command, ["--allow-insecure-http"])

        command_at_insecure_endpoint.body.assert_called_once_with()


class TestRejectInsecureSecretEndpoints:
    @pytest.mark.parametrize(
        "endpoint",
        [
            "https://backend.example",
            "http://localhost:8090",
            "http://127.0.0.1:8090",
            "http://[::1]:8090",
        ],
    )
    def test_accepts_https_and_loopback(self, endpoint: str) -> None:
        reject_insecure_secret_endpoints([URL(endpoint)], allow_insecure_http=False)

    @pytest.mark.parametrize(
        "endpoint",
        [
            "http://backend.example",
            "http://localhost.example",
        ],
    )
    def test_rejects_other_http(self, endpoint: str) -> None:
        with pytest.raises(click.ClickException):
            reject_insecure_secret_endpoints([URL(endpoint)], allow_insecure_http=False)
