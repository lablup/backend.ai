from __future__ import annotations

import asyncio
import json
import stat
import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace

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


def _build_stub_webserver_app() -> web.Application:
    async def _report_api_version(_request: web.Request) -> web.Response:
        return web.json_response({"version": "v9.20250722", "manager": "test"})

    async def _handle_login(request: web.Request) -> web.Response:
        credentials = json.loads(request["payload"] or await request.read())
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
def start_stub_webserver() -> Iterator[Callable[[], URL]]:
    server_loop = asyncio.new_event_loop()
    server_thread = threading.Thread(target=server_loop.run_forever, daemon=True)
    server_thread.start()
    started_servers: list[TestServer] = []

    def _start_stub_webserver() -> URL:
        server = TestServer(_build_stub_webserver_app())
        asyncio.run_coroutine_threadsafe(server.start_server(), server_loop).result()
        started_servers.append(server)
        return server.make_url("/").origin()

    yield _start_stub_webserver
    for server in started_servers:
        asyncio.run_coroutine_threadsafe(server.close(), server_loop).result()
    server_loop.call_soon_threadsafe(server_loop.stop)
    server_thread.join()
    server_loop.close()


@pytest.fixture
def v2_session_dir_before_first_login(
    isolated_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    start_stub_webserver: Callable[[], URL],
) -> Path:
    webserver_url = start_stub_webserver()
    _write_v2_session_config(isolated_home, str(webserver_url))
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
    start_stub_webserver: Callable[[], URL],
) -> Path:
    webserver_url = start_stub_webserver()
    set_config(APIConfig(endpoint=str(webserver_url), endpoint_type="session"))
    state_dir = isolated_home / "state" / "backend.ai"
    monkeypatch.setattr(legacy_cli_config, "local_state_path", state_dir)
    monkeypatch.setattr(legacy_cli_config.getpass, "getpass", lambda: _PASSWORD)
    return state_dir


@pytest.fixture
def legacy_state_dir_holding_loose_files(legacy_state_dir_before_first_login: Path) -> Path:
    _write_loose_file(legacy_state_dir_before_first_login / "cookie.dat", "{}")
    _write_loose_file(legacy_state_dir_before_first_login / "config.json", "{}")
    return legacy_state_dir_before_first_login


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
