from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import click
import pytest
from click.testing import CliRunner
from yarl import URL

from ai.backend.client.cli import config as legacy_cli_config
from ai.backend.client.cli.insecure_http_guard import reject_insecure_password_endpoints
from ai.backend.client.cli.v2 import helpers, login_cmd, v2
from ai.backend.client.config import APIConfig, set_config

_INSECURE_ENDPOINT = "http://backend.example"
_ALLOW_FLAG = "--allow-insecure-http"
_USER_ID = "user@example.com"


@dataclass(frozen=True)
class _AcceptedEndpointsCase:
    endpoints: list[str]
    allow_insecure_http: bool


@dataclass(frozen=True)
class _RejectedEndpointsCase:
    endpoints: list[str]
    expected_refused_endpoints: str


@dataclass(frozen=True)
class _V2LoginAtInsecureEndpoint:
    password_prompt: MagicMock
    login_post: MagicMock


@dataclass(frozen=True)
class _LegacySessionAtInsecureEndpoint:
    password_prompt: MagicMock
    session_factory: MagicMock


@dataclass(frozen=True)
class _LegacyPasswordCommandCase:
    command: click.Command
    arguments: list[str]


@pytest.fixture
def v2_login_at_insecure_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> _V2LoginAtInsecureEndpoint:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv(helpers.PROFILE_ENV, raising=False)
    monkeypatch.setenv("BACKEND_ENDPOINT", _INSECURE_ENDPOINT)
    monkeypatch.setenv("BACKEND_ENDPOINT_TYPE", "session")
    monkeypatch.setenv("BACKEND_USER", _USER_ID)
    monkeypatch.delenv("BACKEND_PASSWORD", raising=False)
    password_prompt = MagicMock(return_value="password")
    monkeypatch.setattr("getpass.getpass", password_prompt)

    registry = MagicMock()
    registry.close = AsyncMock()
    login_post = registry._client.session.post
    login_post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value={"authenticated": True},
    )
    monkeypatch.setattr(login_cmd, "create_v2_registry", AsyncMock(return_value=registry))
    return _V2LoginAtInsecureEndpoint(password_prompt=password_prompt, login_post=login_post)


@pytest.fixture
def legacy_session_at_insecure_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> _LegacySessionAtInsecureEndpoint:
    set_config(APIConfig(endpoint=_INSECURE_ENDPOINT, endpoint_type="session"))
    monkeypatch.setattr(legacy_cli_config, "local_state_path", tmp_path)
    password_prompt = MagicMock(return_value="password")
    monkeypatch.setattr("getpass.getpass", password_prompt)

    session_factory = MagicMock()
    session = session_factory.return_value.__enter__.return_value
    session.Auth.login.return_value = {"authenticated": True, "cookies": {}, "config": {}}
    monkeypatch.setattr(legacy_cli_config, "Session", session_factory)
    return _LegacySessionAtInsecureEndpoint(
        password_prompt=password_prompt,
        session_factory=session_factory,
    )


class TestRejectInsecurePasswordEndpoints:
    @pytest.mark.parametrize(
        "case",
        [
            _AcceptedEndpointsCase(["https://backend.example"], allow_insecure_http=False),
            _AcceptedEndpointsCase(["http://localhost:8090"], allow_insecure_http=False),
            _AcceptedEndpointsCase(["http://127.0.0.1:8090"], allow_insecure_http=False),
            _AcceptedEndpointsCase(["http://127.1.2.3:8090"], allow_insecure_http=False),
            _AcceptedEndpointsCase(["http://[::1]:8090"], allow_insecure_http=False),
            _AcceptedEndpointsCase(
                ["https://backend.example", "http://127.0.0.1:8090"],
                allow_insecure_http=False,
            ),
            _AcceptedEndpointsCase(["http://backend.example"], allow_insecure_http=True),
        ],
        ids=lambda case: f"{','.join(case.endpoints)}-allow={case.allow_insecure_http}",
    )
    def test_accepts_endpoint_that_keeps_the_password_private_or_is_allowed(
        self,
        case: _AcceptedEndpointsCase,
    ) -> None:
        reject_insecure_password_endpoints(
            [URL(endpoint) for endpoint in case.endpoints],
            case.allow_insecure_http,
        )

    @pytest.mark.parametrize(
        "case",
        [
            _RejectedEndpointsCase(
                endpoints=["http://backend.example"],
                expected_refused_endpoints="http://backend.example",
            ),
            _RejectedEndpointsCase(
                endpoints=["http://10.0.0.1:8090"],
                expected_refused_endpoints="http://10.0.0.1:8090",
            ),
            _RejectedEndpointsCase(
                endpoints=["http://localhost.example"],
                expected_refused_endpoints="http://localhost.example",
            ),
            _RejectedEndpointsCase(
                endpoints=[
                    "https://safe.example",
                    "http://first.example",
                    "http://second.example",
                ],
                expected_refused_endpoints="http://first.example, http://second.example",
            ),
        ],
        ids=lambda case: ",".join(case.endpoints),
    )
    def test_rejects_naming_only_the_insecure_endpoints(
        self,
        case: _RejectedEndpointsCase,
    ) -> None:
        with pytest.raises(click.ClickException) as raised:
            reject_insecure_password_endpoints(
                [URL(endpoint) for endpoint in case.endpoints],
                allow_insecure_http=False,
            )

        assert f"to {case.expected_refused_endpoints}:" in raised.value.message


class TestV2Login:
    def test_refuses_before_prompting_or_sending(
        self,
        runner: CliRunner,
        v2_login_at_insecure_endpoint: _V2LoginAtInsecureEndpoint,
    ) -> None:
        result = runner.invoke(v2, ["login"])

        assert result.exit_code == 1
        assert _ALLOW_FLAG in result.output
        assert v2_login_at_insecure_endpoint.password_prompt.call_count == 0
        assert v2_login_at_insecure_endpoint.login_post.call_count == 0

    def test_allow_flag_sends_the_login_request(
        self,
        runner: CliRunner,
        v2_login_at_insecure_endpoint: _V2LoginAtInsecureEndpoint,
    ) -> None:
        result = runner.invoke(v2, ["login", _ALLOW_FLAG])

        assert result.exit_code == 0, result.output
        assert v2_login_at_insecure_endpoint.login_post.call_count == 1


class TestLegacyPasswordCommands:
    @pytest.mark.parametrize(
        "case",
        [
            _LegacyPasswordCommandCase(command=legacy_cli_config.login, arguments=[]),
            _LegacyPasswordCommandCase(
                command=legacy_cli_config.update_password,
                arguments=["old-password", "new-password", "new-password"],
            ),
            _LegacyPasswordCommandCase(
                command=legacy_cli_config.update_password_no_auth,
                arguments=["default", _USER_ID, "old-password", "new-password"],
            ),
        ],
        ids=lambda case: case.command.name,
    )
    def test_refuses_before_prompting_or_opening_a_session(
        self,
        runner: CliRunner,
        legacy_session_at_insecure_endpoint: _LegacySessionAtInsecureEndpoint,
        case: _LegacyPasswordCommandCase,
    ) -> None:
        result = runner.invoke(case.command, case.arguments, input=f"{_USER_ID}\n")

        assert result.exit_code == 1
        assert _ALLOW_FLAG in result.output
        assert legacy_session_at_insecure_endpoint.password_prompt.call_count == 0
        assert legacy_session_at_insecure_endpoint.session_factory.call_count == 0

    @pytest.mark.parametrize(
        "case",
        [
            _LegacyPasswordCommandCase(command=legacy_cli_config.login, arguments=[]),
            _LegacyPasswordCommandCase(
                command=legacy_cli_config.update_password,
                arguments=["old-password", "new-password", "new-password"],
            ),
            _LegacyPasswordCommandCase(
                command=legacy_cli_config.update_password_no_auth,
                arguments=["default", _USER_ID, "old-password", "new-password"],
            ),
        ],
        ids=lambda case: case.command.name,
    )
    def test_allow_flag_opens_a_session(
        self,
        runner: CliRunner,
        legacy_session_at_insecure_endpoint: _LegacySessionAtInsecureEndpoint,
        case: _LegacyPasswordCommandCase,
    ) -> None:
        result = runner.invoke(
            case.command,
            [*case.arguments, _ALLOW_FLAG],
            input=f"{_USER_ID}\n",
        )

        assert result.exit_code == 0, result.output
        assert legacy_session_at_insecure_endpoint.session_factory.call_count == 1
