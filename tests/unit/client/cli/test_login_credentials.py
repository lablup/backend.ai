from __future__ import annotations

import asyncio
import json
import ssl
import stat
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Protocol

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from click.testing import CliRunner
from yarl import URL

from ai.backend.client.cli import config as legacy_cli_config
from ai.backend.client.cli.v2 import v2
from ai.backend.client.config import APIConfig, set_config
from ai.backend.web.proxy import decrypt_payload

_USERNAME = "user@example.com"
_PASSWORD = "s3cret-passw0rd"
_OTP = "123456"
_LOGIN_PAYLOAD = {"username": _USERNAME, "password": _PASSWORD}
_LOGIN_PAYLOAD_WITH_OTP = {"username": _USERNAME, "password": _PASSWORD, "otp": _OTP}


@dataclass(frozen=True)
class _ReceivedLoginRequest:
    encoded_header: str | None
    raw_body: bytes
    credentials: dict[str, Any]


@dataclass(frozen=True)
class _StubWebserver:
    url: URL
    received_login_requests: list[_ReceivedLoginRequest]


class _StubWebserverStarter(Protocol):
    def __call__(
        self,
        *,
        otp_required: bool = False,
        tls_context: ssl.SSLContext | None = None,
    ) -> _StubWebserver: ...


@dataclass(frozen=True)
class _LoginRequestCase:
    scheme: str
    endpoint_suffix: str
    otp_required: bool
    expected_payloads: list[dict[str, str]]


def _build_stub_webserver_app(
    otp_required: bool,
    received_login_requests: list[_ReceivedLoginRequest],
) -> web.Application:
    async def _report_api_version(_request: web.Request) -> web.Response:
        return web.json_response({"version": "v9.20250722", "manager": "test"})

    async def _handle_login(request: web.Request) -> web.Response:
        raw_body = await request.read()
        credentials = json.loads(request["payload"] or raw_body)
        received_login_requests.append(
            _ReceivedLoginRequest(
                encoded_header=request.headers.get("X-BackendAI-Encoded"),
                raw_body=raw_body,
                credentials=credentials,
            )
        )
        if otp_required and "otp" not in credentials:
            return web.json_response({
                "authenticated": False,
                "data": {"details": "OTP not provided"},
            })
        response = web.json_response({
            "authenticated": True,
            "config": {"username": credentials["username"]},
        })
        response.set_cookie("session", "session-id")
        return response

    app = web.Application(middlewares=[decrypt_payload])
    app["config"] = SimpleNamespace(service=SimpleNamespace(force_endpoint_protocol=None))
    app.router.add_get("/func/", _report_api_version)
    app.router.add_post("/server/login", _handle_login)
    return app


def _write_loose_file(file_path: Path, content: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    file_path.chmod(0o644)


def _write_v2_session_config(home: Path, endpoint: str) -> None:
    config_dir = home / ".backend.ai"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "[backend-ai]\n"
        f'endpoint = "{endpoint}"\n'
        'endpoint_type = "session"\n'
        "skip_ssl_verification = true\n"
    )


@pytest.fixture
def start_stub_webserver() -> Iterator[_StubWebserverStarter]:
    server_loop = asyncio.new_event_loop()
    server_thread = threading.Thread(target=server_loop.run_forever, daemon=True)
    server_thread.start()
    started_servers: list[TestServer] = []

    def _start_stub_webserver(
        *,
        otp_required: bool = False,
        tls_context: ssl.SSLContext | None = None,
    ) -> _StubWebserver:
        received_login_requests: list[_ReceivedLoginRequest] = []
        server = TestServer(_build_stub_webserver_app(otp_required, received_login_requests))
        asyncio.run_coroutine_threadsafe(server.start_server(ssl=tls_context), server_loop).result()
        started_servers.append(server)
        return _StubWebserver(
            url=server.make_url("/").origin(),
            received_login_requests=received_login_requests,
        )

    yield _start_stub_webserver
    for server in started_servers:
        asyncio.run_coroutine_threadsafe(server.close(), server_loop).result()
    server_loop.call_soon_threadsafe(server_loop.stop)
    server_thread.join()
    server_loop.close()


@pytest.fixture
def webserver_for_login_request_case(
    case: _LoginRequestCase,
    isolated_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    self_signed_tls_context: ssl.SSLContext,
    start_stub_webserver: _StubWebserverStarter,
) -> _StubWebserver:
    webserver = start_stub_webserver(
        otp_required=case.otp_required,
        tls_context=self_signed_tls_context if case.scheme == "https" else None,
    )
    _write_v2_session_config(isolated_home, f"{webserver.url}{case.endpoint_suffix}")
    monkeypatch.setenv("BACKEND_USER", _USERNAME)
    monkeypatch.setenv("BACKEND_PASSWORD", _PASSWORD)
    return webserver


@pytest.fixture
def v2_session_dir_before_first_login(
    isolated_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    start_stub_webserver: _StubWebserverStarter,
) -> Path:
    webserver = start_stub_webserver()
    _write_v2_session_config(isolated_home, str(webserver.url))
    monkeypatch.setenv("BACKEND_USER", _USERNAME)
    monkeypatch.setenv("BACKEND_PASSWORD", _PASSWORD)
    return isolated_home / ".backend.ai" / "session"


@pytest.fixture
def v2_session_dir_holding_loose_files(v2_session_dir_before_first_login: Path) -> Path:
    _write_loose_file(v2_session_dir_before_first_login / "cookie.dat", "{}")
    _write_loose_file(v2_session_dir_before_first_login / "config.json", "{}")
    return v2_session_dir_before_first_login


@pytest.fixture
def legacy_state_dir_before_first_login(
    isolated_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    start_stub_webserver: _StubWebserverStarter,
) -> Path:
    webserver = start_stub_webserver()
    set_config(APIConfig(endpoint=str(webserver.url), endpoint_type="session"))
    state_dir = isolated_home / "state" / "backend.ai"
    monkeypatch.setattr(legacy_cli_config, "local_state_path", state_dir)
    monkeypatch.setattr(legacy_cli_config.getpass, "getpass", lambda: _PASSWORD)
    return state_dir


@pytest.fixture
def legacy_state_dir_holding_loose_files(legacy_state_dir_before_first_login: Path) -> Path:
    _write_loose_file(legacy_state_dir_before_first_login / "cookie.dat", "{}")
    _write_loose_file(legacy_state_dir_before_first_login / "config.json", "{}")
    return legacy_state_dir_before_first_login


class TestV2LoginRequestBody:
    @pytest.mark.parametrize(
        "case",
        [
            _LoginRequestCase(
                scheme="http",
                endpoint_suffix="",
                otp_required=False,
                expected_payloads=[_LOGIN_PAYLOAD],
            ),
            _LoginRequestCase(
                scheme="http",
                endpoint_suffix="/",
                otp_required=False,
                expected_payloads=[_LOGIN_PAYLOAD],
            ),
            _LoginRequestCase(
                scheme="http",
                endpoint_suffix="",
                otp_required=True,
                expected_payloads=[_LOGIN_PAYLOAD, _LOGIN_PAYLOAD_WITH_OTP],
            ),
            _LoginRequestCase(
                scheme="http",
                endpoint_suffix="/",
                otp_required=True,
                expected_payloads=[_LOGIN_PAYLOAD, _LOGIN_PAYLOAD_WITH_OTP],
            ),
        ],
        ids=lambda case: f"suffix={case.endpoint_suffix!r}-otp={case.otp_required}",
    )
    def test_http_sends_encoded_body_the_webserver_can_decrypt(
        self,
        runner: CliRunner,
        webserver_for_login_request_case: _StubWebserver,
        case: _LoginRequestCase,
    ) -> None:
        result = runner.invoke(v2, ["login"], input=f"{_OTP}\n")

        assert result.exit_code == 0, result.output
        received = webserver_for_login_request_case.received_login_requests
        assert [request.credentials for request in received] == case.expected_payloads
        assert [request.encoded_header for request in received] == ["true"] * len(received)
        assert not any(_PASSWORD.encode() in request.raw_body for request in received)

    @pytest.mark.parametrize(
        "case",
        [
            _LoginRequestCase(
                scheme="https",
                endpoint_suffix="",
                otp_required=False,
                expected_payloads=[_LOGIN_PAYLOAD],
            ),
            _LoginRequestCase(
                scheme="https",
                endpoint_suffix="",
                otp_required=True,
                expected_payloads=[_LOGIN_PAYLOAD, _LOGIN_PAYLOAD_WITH_OTP],
            ),
        ],
        ids=lambda case: f"otp={case.otp_required}",
    )
    def test_https_sends_plain_json(
        self,
        runner: CliRunner,
        webserver_for_login_request_case: _StubWebserver,
        case: _LoginRequestCase,
    ) -> None:
        result = runner.invoke(v2, ["login"], input=f"{_OTP}\n")

        assert result.exit_code == 0, result.output
        received = webserver_for_login_request_case.received_login_requests
        assert [json.loads(request.raw_body) for request in received] == case.expected_payloads
        assert [request.encoded_header for request in received] == [None] * len(received)


class TestV2LoginSessionFiles:
    def test_new_files_are_owner_only_in_owner_only_directory(
        self,
        runner: CliRunner,
        v2_session_dir_before_first_login: Path,
    ) -> None:
        result = runner.invoke(v2, ["login"])

        assert result.exit_code == 0, result.output
        session_dir = v2_session_dir_before_first_login
        assert stat.S_IMODE(session_dir.stat().st_mode) == 0o700
        assert stat.S_IMODE((session_dir / "cookie.dat").stat().st_mode) == 0o600
        assert stat.S_IMODE((session_dir / "config.json").stat().st_mode) == 0o600

    def test_loose_existing_files_are_tightened(
        self,
        runner: CliRunner,
        v2_session_dir_holding_loose_files: Path,
    ) -> None:
        result = runner.invoke(v2, ["login"])

        assert result.exit_code == 0, result.output
        session_dir = v2_session_dir_holding_loose_files
        assert stat.S_IMODE((session_dir / "cookie.dat").stat().st_mode) == 0o600
        assert stat.S_IMODE((session_dir / "config.json").stat().st_mode) == 0o600


class TestLegacyLoginSessionFiles:
    def test_new_files_are_owner_only_in_owner_only_directories(
        self,
        runner: CliRunner,
        legacy_state_dir_before_first_login: Path,
    ) -> None:
        result = runner.invoke(legacy_cli_config.login, input=f"{_USERNAME}\n")

        assert result.exit_code == 0, result.output
        state_dir = legacy_state_dir_before_first_login
        assert stat.S_IMODE(state_dir.parent.stat().st_mode) == 0o700
        assert stat.S_IMODE(state_dir.stat().st_mode) == 0o700
        assert stat.S_IMODE((state_dir / "cookie.dat").stat().st_mode) == 0o600
        assert stat.S_IMODE((state_dir / "config.json").stat().st_mode) == 0o600

    def test_loose_existing_files_are_tightened(
        self,
        runner: CliRunner,
        legacy_state_dir_holding_loose_files: Path,
    ) -> None:
        result = runner.invoke(legacy_cli_config.login, input=f"{_USERNAME}\n")

        assert result.exit_code == 0, result.output
        state_dir = legacy_state_dir_holding_loose_files
        assert stat.S_IMODE((state_dir / "cookie.dat").stat().st_mode) == 0o600
        assert stat.S_IMODE((state_dir / "config.json").stat().st_mode) == 0o600
