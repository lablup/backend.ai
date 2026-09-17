"""Tests for v2 CLI profiles (BA-7947)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import Any

import click
import pytest
from click.testing import CliRunner, Result

from ai.backend.client.cli.v2 import helpers, login_cmd

PASSWORD = "s3cret-passw0rd"


class _FakeResponse:
    async def __aenter__(self) -> _FakeResponse:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def json(self) -> dict[str, Any]:
        return {"authenticated": True, "config": {"mode": "fake"}}


class _FakeCookieJar:
    _user: str

    def __init__(self, user: str) -> None:
        self._user = user

    def save(self, path: Path) -> None:
        path.write_text(f"cookie-of-{self._user}")


class _FakeSession:
    cookie_jar: _FakeCookieJar | None

    def __init__(self) -> None:
        self.cookie_jar = None

    def post(self, url: str, json: dict[str, Any]) -> _FakeResponse:
        self.cookie_jar = _FakeCookieJar(str(json["username"]))
        return _FakeResponse()


class _FakeClient:
    session: _FakeSession

    def __init__(self) -> None:
        self.session = _FakeSession()

    def build_url_raw(self, path: str) -> str:
        return path


class _FakeRegistry:
    _client: _FakeClient

    def __init__(self) -> None:
        self._client = _FakeClient()

    async def close(self) -> None:
        return None


@pytest.fixture
def home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Isolated ``HOME`` and cwd with no ``BACKEND_*`` variables."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    for key in (
        helpers.PROFILE_ENV,
        "BACKEND_ENDPOINT",
        "BACKEND_ENDPOINT_TYPE",
        "BACKEND_ACCESS_KEY",
        "BACKEND_SECRET_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    return tmp_path


@pytest.fixture
def bai(
    runner: CliRunner,
    cli_entrypoint: Callable[[], click.Group],
    home: Path,
) -> Callable[..., Result]:
    def _invoke(*args: str) -> Result:
        return runner.invoke(cli_entrypoint, ["v2", *args])

    return _invoke


@pytest.fixture
def two_profiles(bai: Callable[..., Result]) -> None:
    for name in ("a", "b"):
        result = bai(
            "profile",
            "create",
            name,
            "--endpoint",
            f"https://{name}.example",
            "--endpoint-type",
            "session",
        )
        assert result.exit_code == 0, result.output


class TestLegacy:
    def test_no_profile_reads_legacy_files(self, bai: Callable[..., Result], home: Path) -> None:
        legacy = home / ".backend.ai"
        legacy.mkdir()
        (legacy / "config.toml").write_text('[backend-ai]\nendpoint = "https://legacy.example"\n')
        (legacy / "credentials.toml").write_text('[backend-ai]\naccess_key = "AKLEGACY"\n')

        result = bai("config", "show")

        assert result.exit_code == 0, result.output
        assert "https://legacy.example" in result.output
        assert "AKLEGACY" in result.output
        assert "(default)" in result.output

    def test_config_set_writes_legacy_file(self, bai: Callable[..., Result], home: Path) -> None:
        result = bai("config", "set", "endpoint", "https://legacy.example")

        assert result.exit_code == 0, result.output
        assert "https://legacy.example" in (home / ".backend.ai" / "config.toml").read_text()
        assert not (home / ".backend.ai" / "profiles").exists()


@pytest.mark.usefixtures("two_profiles")
class TestSelection:
    def test_current_profile_file(self, bai: Callable[..., Result]) -> None:
        assert bai("profile", "use", "a").exit_code == 0

        assert bai("config", "get", "endpoint").output.strip() == "https://a.example"

    def test_env_over_current_profile(
        self, bai: Callable[..., Result], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bai("profile", "use", "a")
        monkeypatch.setenv(helpers.PROFILE_ENV, "b")

        assert bai("config", "get", "endpoint").output.strip() == "https://b.example"

    def test_option_over_env(
        self, bai: Callable[..., Result], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(helpers.PROFILE_ENV, "b")

        result = bai("--profile", "a", "config", "get", "endpoint")

        assert result.output.strip() == "https://a.example"

    def test_endpoint_env_overrides_selected_profile(
        self, bai: Callable[..., Result], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BACKEND_ENDPOINT", "https://env.example")

        result = bai("--profile", "a", "config", "get", "endpoint")

        assert result.output.strip() == "https://env.example"

    def test_config_set_targets_selected_profile(
        self, bai: Callable[..., Result], home: Path
    ) -> None:
        result = bai("--profile", "b", "config", "set", "access-key", "AKB")

        assert result.exit_code == 0, result.output
        assert "AKB" in (home / ".backend.ai/profiles/b/credentials.toml").read_text()
        assert not (home / ".backend.ai/credentials.toml").exists()

    @pytest.mark.parametrize("source", ["option", "env", "current-profile"])
    def test_missing_profile_fails(
        self,
        bai: Callable[..., Result],
        home: Path,
        monkeypatch: pytest.MonkeyPatch,
        source: str,
    ) -> None:
        args: list[str] = []
        match source:
            case "option":
                args = ["--profile", "nope"]
            case "env":
                monkeypatch.setenv(helpers.PROFILE_ENV, "nope")
            case _:
                (home / ".backend.ai/current-profile").write_text("nope\n")

        result = bai(*args, "config", "show")

        assert result.exit_code == 1
        assert "'nope' does not exist" in result.output


@pytest.mark.usefixtures("two_profiles")
class TestLogin:
    @pytest.fixture(autouse=True)
    def fake_server(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def _create(_config: helpers.V2ConnectionConfig) -> _FakeRegistry:
            return _FakeRegistry()

        monkeypatch.setattr(login_cmd, "create_v2_registry", _create)
        monkeypatch.setenv("BACKEND_PASSWORD", PASSWORD)

    def test_cookies_are_kept_per_profile(
        self, bai: Callable[..., Result], home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for name in ("a", "b"):
            monkeypatch.setenv("BACKEND_USER", f"user-{name}")
            result = bai("--profile", name, "login")
            assert result.exit_code == 0, result.output

        profiles = home / ".backend.ai/profiles"
        assert (profiles / "a/session/cookie.dat").read_text() == "cookie-of-user-a"
        assert (profiles / "b/session/cookie.dat").read_text() == "cookie-of-user-b"
        assert not (home / ".backend.ai/session").exists()

    def test_password_is_not_stored(
        self, bai: Callable[..., Result], home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BACKEND_USER", "user-a")
        assert bai("--profile", "a", "login").exit_code == 0

        files = [p for p in (home / ".backend.ai").rglob("*") if p.is_file()]
        assert files
        assert all(PASSWORD not in p.read_text() for p in files)

    def test_logout_clears_selected_profile_only(
        self, bai: Callable[..., Result], home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for name in ("a", "b"):
            monkeypatch.setenv("BACKEND_USER", f"user-{name}")
            bai("--profile", name, "login")

        assert bai("--profile", "a", "logout").exit_code == 0

        profiles = home / ".backend.ai/profiles"
        assert not (profiles / "a/session/cookie.dat").exists()
        assert (profiles / "b/session/cookie.dat").exists()


class TestProfileCommands:
    def test_create_twice_fails(self, bai: Callable[..., Result]) -> None:
        assert bai("profile", "create", "a").exit_code == 0

        result = bai("profile", "create", "a")

        assert result.exit_code == 1
        assert "already exists" in result.output

    @pytest.mark.parametrize("name", ["../escape", ".hidden", "a/b"])
    def test_create_rejects_invalid_name(self, bai: Callable[..., Result], name: str) -> None:
        result = bai("profile", "create", name)

        assert result.exit_code == 1
        assert "Invalid profile name" in result.output

    def test_use_missing_profile_fails(self, bai: Callable[..., Result], home: Path) -> None:
        result = bai("profile", "use", "nope")

        assert result.exit_code == 1
        assert not (home / ".backend.ai/current-profile").exists()

    @pytest.mark.usefixtures("two_profiles")
    def test_list_marks_selected(self, bai: Callable[..., Result]) -> None:
        bai("profile", "use", "b")

        lines = bai("profile", "list").output.splitlines()

        assert lines == ["  a\thttps://a.example", "* b\thttps://b.example"]

    @pytest.mark.usefixtures("two_profiles")
    def test_show_named_profile(self, bai: Callable[..., Result]) -> None:
        result = bai("profile", "show", "b")

        assert result.exit_code == 0, result.output
        assert "https://b.example" in result.output

    @pytest.mark.usefixtures("two_profiles")
    def test_delete_current_resets_current_profile(
        self, bai: Callable[..., Result], home: Path
    ) -> None:
        bai("profile", "use", "a")

        result = bai("profile", "delete", "a", "--yes")

        assert result.exit_code == 0, result.output
        assert not (home / ".backend.ai/profiles/a").exists()
        assert not (home / ".backend.ai/current-profile").exists()

    @pytest.mark.usefixtures("two_profiles")
    def test_delete_declined_keeps_profile(self, bai: Callable[..., Result], home: Path) -> None:
        result = bai("profile", "delete", "a")

        assert result.exit_code == 1
        assert (home / ".backend.ai/profiles/a").is_dir()

    @pytest.mark.usefixtures("two_profiles")
    def test_rename_current_updates_current_profile(
        self, bai: Callable[..., Result], home: Path
    ) -> None:
        bai("profile", "use", "a")

        result = bai("profile", "rename", "a", "c")

        assert result.exit_code == 0, result.output
        assert (home / ".backend.ai/profiles/c/config.toml").exists()
        assert (home / ".backend.ai/current-profile").read_text().strip() == "c"

    @pytest.mark.usefixtures("two_profiles")
    def test_rename_onto_existing_fails(self, bai: Callable[..., Result]) -> None:
        result = bai("profile", "rename", "a", "b")

        assert result.exit_code == 1
        assert "already exists" in result.output
