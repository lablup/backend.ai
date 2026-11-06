from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock

import click
import pytest
from click.testing import CliRunner
from yarl import URL

from ai.backend.client.cli.v2 import config_cmd, helpers, login_cmd, v2
from ai.backend.client.cli.v2.helpers import (
    V2ConnectionConfig,
    create_v2_registry,
    load_v2_config,
)
from ai.backend.client.cli.v2.insecure_http_guard import (
    ALLOW_INSECURE_HTTP_ENV,
    reject_insecure_endpoint,
)
from ai.backend.client.v2.v2_registry import V2ClientRegistry


@pytest.fixture
def registry_create(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    create = AsyncMock()
    monkeypatch.setattr(V2ClientRegistry, "create", create)
    return create


@pytest.fixture
def v2_config_at_insecure_endpoint() -> V2ConnectionConfig:
    return V2ConnectionConfig(
        endpoint=URL("http://backend.example"),
        endpoint_type="api",
        access_key=None,
        secret_key=None,
        api_version="v9.20250722",
    )


@pytest.fixture
def config_dir_at_insecure_endpoint(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    session_dir = tmp_path / "session"
    cookie_file = session_dir / "cookie.dat"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(helpers, "CONFIG_FILE", config_file)
    monkeypatch.setattr(helpers, "CREDENTIALS_FILE", tmp_path / "credentials.toml")
    monkeypatch.setattr(helpers, "COOKIE_FILE", cookie_file)
    monkeypatch.setattr(config_cmd, "CONFIG_FILE", config_file)
    monkeypatch.setattr(login_cmd, "SESSION_DIR", session_dir)
    monkeypatch.setattr(login_cmd, "COOKIE_FILE", cookie_file)
    monkeypatch.delenv(ALLOW_INSECURE_HTTP_ENV, raising=False)
    monkeypatch.setenv("BACKEND_ENDPOINT", "http://backend.example")
    monkeypatch.setenv("BACKEND_ENDPOINT_TYPE", "session")


@pytest.fixture
def stored_session_cookie_at_insecure_endpoint(config_dir_at_insecure_endpoint: None) -> Path:
    helpers.COOKIE_FILE.parent.mkdir(parents=True)
    helpers.COOKIE_FILE.write_text("cookie")
    return helpers.COOKIE_FILE


@pytest.mark.usefixtures("config_dir_at_insecure_endpoint")
class TestAllowInsecureHttpSetting:
    def test_environment_variable_allows_it(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")

        assert load_v2_config().allow_insecure_http is True

    def test_config_set_allows_it(self) -> None:
        result = CliRunner().invoke(v2, ["config", "set", "allow-insecure-http", "true"])

        assert result.exit_code == 0, result.output
        assert load_v2_config().allow_insecure_http is True


class TestLogout:
    def test_removes_the_stored_cookie_when_the_endpoint_is_refused(
        self,
        stored_session_cookie_at_insecure_endpoint: Path,
    ) -> None:
        result = CliRunner().invoke(v2, ["logout"])

        assert result.exit_code == 0, result.output
        assert not stored_session_cookie_at_insecure_endpoint.exists()


class TestCreateV2Registry:
    async def test_refuses_an_insecure_endpoint(
        self,
        registry_create: AsyncMock,
        v2_config_at_insecure_endpoint: V2ConnectionConfig,
    ) -> None:
        with pytest.raises(click.ClickException):
            await create_v2_registry(v2_config_at_insecure_endpoint)

        registry_create.assert_not_called()

    async def test_creates_the_registry_when_insecure_http_is_allowed(
        self,
        registry_create: AsyncMock,
        v2_config_at_insecure_endpoint: V2ConnectionConfig,
    ) -> None:
        await create_v2_registry(replace(v2_config_at_insecure_endpoint, allow_insecure_http=True))

        registry_create.assert_called_once()


class TestRejectInsecureEndpoint:
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
        reject_insecure_endpoint(URL(endpoint), allow_insecure_http=False)

    @pytest.mark.parametrize(
        "endpoint",
        [
            "http://backend.example",
            "http://localhost.example",
        ],
    )
    def test_rejects_other_http(self, endpoint: str) -> None:
        with pytest.raises(click.ClickException):
            reject_insecure_endpoint(URL(endpoint), allow_insecure_http=False)
