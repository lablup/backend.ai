"""Alembic config / database URL resolution for the ``mgr schema`` commands."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner
from sqlalchemy.engine import make_url

from ai.backend.common.typed_validators import HostPortPair
from ai.backend.manager.cli.alembic_config import (
    MANAGER_SCRIPT_LOCATION,
    build_db_url,
    load_alembic_config,
    resolve_alembic_config,
)
from ai.backend.manager.cli.dbschema import cli as schema_cli
from ai.backend.manager.config.unified import DatabaseConfig
from ai.backend.manager.errors.resource import ConfigurationLoadFailed

FILE_URL = "postgresql+asyncpg://fileuser:filepass@filehost:6543/filedb"
TRICKY_PASSWORD = "p@ss:w/rd%"


def _write_ini(path: Path, *, sqlalchemy_url: str | None) -> Path:
    lines = ["[alembic]", "script_location = ai.backend.manager.models:alembic"]
    if sqlalchemy_url is not None:
        lines.append(f"sqlalchemy.url = {sqlalchemy_url}")
    path.write_text("\n".join(lines) + "\n")
    return path


@pytest.fixture
def workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def db_config() -> DatabaseConfig:
    return DatabaseConfig.model_validate({
        "addr": HostPortPair(host="db.example.com", port=15432),
        "name": "backend",
        "user": "bai",
        "password": TRICKY_PASSWORD,
    })


@pytest.fixture
def db_config_loader(db_config: DatabaseConfig) -> AsyncMock:
    return AsyncMock(return_value=db_config)


@pytest.fixture
def ini_with_url(workdir: Path) -> Path:
    return _write_ini(workdir / "explicit.ini", sqlalchemy_url=FILE_URL)


@pytest.fixture
def ini_without_url(workdir: Path) -> Path:
    return _write_ini(workdir / "no-url.ini", sqlalchemy_url=None)


@pytest.fixture
def cwd_default_ini(workdir: Path) -> Path:
    return _write_ini(workdir / "alembic.ini", sqlalchemy_url=FILE_URL)


class TestBuildDbUrl:
    def test_special_characters_in_password_round_trip(self, db_config: DatabaseConfig) -> None:
        url = build_db_url(db_config)

        parsed = make_url(url.render_as_string(hide_password=False))
        assert parsed.password == TRICKY_PASSWORD
        assert parsed.drivername == "postgresql+asyncpg"
        assert (parsed.host, parsed.port, parsed.database, parsed.username) == (
            "db.example.com",
            15432,
            "backend",
            "bai",
        )

    def test_password_is_hidden_when_rendered_for_logs(self, db_config: DatabaseConfig) -> None:
        assert TRICKY_PASSWORD not in build_db_url(db_config).render_as_string(hide_password=True)


class TestResolveAlembicConfig:
    async def test_explicit_file_url_wins(
        self, ini_with_url: Path, db_config_loader: AsyncMock
    ) -> None:
        resolved = await resolve_alembic_config(ini_with_url, db_config_loader)

        assert resolved.db_url == make_url(FILE_URL)
        assert resolved.config.config_file_name == str(ini_with_url)
        db_config_loader.assert_not_awaited()

    async def test_explicit_file_without_url_falls_back_to_manager_config(
        self, ini_without_url: Path, db_config_loader: AsyncMock, db_config: DatabaseConfig
    ) -> None:
        resolved = await resolve_alembic_config(ini_without_url, db_config_loader)

        assert resolved.db_url == build_db_url(db_config)
        assert resolved.config.config_file_name == str(ini_without_url)

    async def test_default_ini_in_cwd_is_used(
        self, cwd_default_ini: Path, db_config_loader: AsyncMock
    ) -> None:
        resolved = await resolve_alembic_config(None, db_config_loader)

        assert resolved.db_url == make_url(FILE_URL)
        assert resolved.config.config_file_name == "alembic.ini"
        db_config_loader.assert_not_awaited()

    async def test_no_file_builds_config_from_packaged_scripts_and_manager_config(
        self, workdir: Path, db_config_loader: AsyncMock, db_config: DatabaseConfig
    ) -> None:
        resolved = await resolve_alembic_config(None, db_config_loader)

        assert resolved.config.config_file_name is None
        assert resolved.config.get_main_option("script_location") == MANAGER_SCRIPT_LOCATION
        assert resolved.db_url == build_db_url(db_config)

    async def test_config_url_survives_ini_interpolation(
        self, workdir: Path, db_config_loader: AsyncMock
    ) -> None:
        resolved = await resolve_alembic_config(None, db_config_loader)

        # env.py reads the URL back through ConfigParser interpolation.
        section = resolved.config.get_section(resolved.config.config_ini_section)
        assert section is not None
        assert make_url(section["sqlalchemy.url"]).password == TRICKY_PASSWORD

    async def test_plain_postgresql_driver_is_switched_to_asyncpg(
        self, workdir: Path, db_config_loader: AsyncMock
    ) -> None:
        ini = _write_ini(workdir / "sync.ini", sqlalchemy_url="postgresql://u:p@h:5432/d")

        resolved = await resolve_alembic_config(ini, db_config_loader)

        assert resolved.db_url.drivername == "postgresql+asyncpg"

    async def test_invalid_file_url_raises(
        self, workdir: Path, db_config_loader: AsyncMock
    ) -> None:
        ini = _write_ini(workdir / "bad.ini", sqlalchemy_url="not a url")

        with pytest.raises(ConfigurationLoadFailed):
            await resolve_alembic_config(ini, db_config_loader)


class TestLoadAlembicConfig:
    def test_no_file_points_at_packaged_scripts(self, workdir: Path) -> None:
        config = load_alembic_config(None)

        assert config.config_file_name is None
        assert config.get_main_option("script_location") == MANAGER_SCRIPT_LOCATION


class _FakeAsyncConnection:
    sync_connection: object

    def __init__(self) -> None:
        self.sync_connection = object()

    async def run_sync(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        return fn(self.sync_connection, *args, **kwargs)


class _FakeEngine:
    connection: _FakeAsyncConnection
    dispose: AsyncMock

    def __init__(self) -> None:
        self.connection = _FakeAsyncConnection()
        self.dispose = AsyncMock()

    @asynccontextmanager
    async def begin(self) -> AsyncIterator[_FakeAsyncConnection]:
        yield self.connection


class TestSchemaUpgradeCommand:
    @pytest.fixture
    def cli_obj(self, db_config: DatabaseConfig) -> MagicMock:
        obj = MagicMock()
        obj.get_bootstrap_config = AsyncMock(return_value=SimpleNamespace(db=db_config))
        return obj

    def test_help_lists_the_revision_argument(self) -> None:
        result = CliRunner().invoke(schema_cli, ["upgrade", "--help"])

        assert result.exit_code == 0, result.output
        assert "[REVISION]" in result.output
        assert "--alembic-config" in result.output

    @pytest.mark.parametrize(
        ("args", "expected_revision"),
        [([], "head"), (["abc123"], "abc123")],
    )
    def test_upgrade_runs_on_a_shared_connection_without_an_ini(
        self,
        workdir: Path,
        cli_obj: MagicMock,
        db_config: DatabaseConfig,
        args: list[str],
        expected_revision: str,
    ) -> None:
        engine = _FakeEngine()
        with (
            patch(
                "ai.backend.manager.repositories.db.engine.create_async_engine",
                return_value=engine,
            ) as create_engine,
            patch("alembic.command.upgrade") as alembic_upgrade,
        ):
            result = CliRunner().invoke(schema_cli, ["upgrade", *args], obj=cli_obj)

        assert result.exit_code == 0, result.output
        create_engine.assert_called_once_with(build_db_url(db_config))
        alembic_upgrade.assert_called_once()
        alembic_cfg, revision = alembic_upgrade.call_args.args
        assert revision == expected_revision
        assert alembic_cfg.attributes["connection"] is engine.connection.sync_connection
        assert alembic_cfg.get_main_option("script_location") == MANAGER_SCRIPT_LOCATION
        engine.dispose.assert_awaited_once()
