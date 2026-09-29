"""Alembic config / database URL resolution for the ``mgr schema`` commands."""

from __future__ import annotations

import importlib.resources
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, override
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner
from sqlalchemy.engine import make_url

from ai.backend.common.json import load_json
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.manager.cli.agent import cli as agent_cli
from ai.backend.manager.cli.alembic_config import (
    MANAGER_SCRIPT_LOCATION,
    build_db_url,
    load_alembic_config,
    resolve_alembic_config,
)
from ai.backend.manager.cli.dbschema import RevisionHistory
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


@pytest.fixture
def cli_obj(db_config: DatabaseConfig) -> MagicMock:
    """A ``CLIContext``-like object shared by the command-level tests below."""
    obj = MagicMock()
    obj.get_bootstrap_config = AsyncMock(
        return_value=SimpleNamespace(
            db=db_config,
            manager=SimpleNamespace(rpc_auth_manager_keypair="dummy-keypair-path"),
        )
    )
    return obj


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

    async def test_explicit_file_wins_over_cwd_default_ini(
        self, workdir: Path, db_config_loader: AsyncMock
    ) -> None:
        # Both an explicitly-given file and a ./alembic.ini exist; -f must win.
        explicit = _write_ini(workdir / "explicit.ini", sqlalchemy_url=FILE_URL)
        _write_ini(
            workdir / "alembic.ini",
            sqlalchemy_url="postgresql+asyncpg://other:other@otherhost:1111/otherdb",
        )

        resolved = await resolve_alembic_config(explicit, db_config_loader)

        assert resolved.db_url == make_url(FILE_URL)
        assert resolved.config.config_file_name == str(explicit)
        db_config_loader.assert_not_awaited()

    async def test_file_url_with_percent_encoded_password_round_trips(
        self, workdir: Path, db_config_loader: AsyncMock
    ) -> None:
        # ConfigParser interpolates '%', so a literal '%' in the file must be
        # doubled; the resulting option must stay a valid, parseable URL.
        ini = _write_ini(
            workdir / "percent.ini",
            sqlalchemy_url="postgresql+asyncpg://user:p%%40ss%%25x@host:5432/db",
        )

        resolved = await resolve_alembic_config(ini, db_config_loader)

        assert resolved.db_url.password == "p@ss%x"
        raw_url = resolved.config.get_main_option("sqlalchemy.url")
        assert raw_url is not None
        assert make_url(raw_url).password == "p@ss%x"


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


class TestSchemaShowCommand:
    def test_show_resolves_config_from_the_resolver(
        self, workdir: Path, cli_obj: MagicMock, db_config: DatabaseConfig
    ) -> None:
        engine = _FakeEngine()
        migration_context = MagicMock()
        migration_context.get_current_revision.return_value = "abc123"
        script = MagicMock()
        script.get_heads.return_value = ["headrev"]
        with (
            patch(
                "ai.backend.manager.repositories.db.engine.create_async_engine",
                return_value=engine,
            ) as create_engine,
            patch(
                "alembic.runtime.migration.MigrationContext.configure",
                return_value=migration_context,
            ),
            patch("alembic.script.ScriptDirectory.from_config", return_value=script),
        ):
            result = CliRunner().invoke(schema_cli, ["show"], obj=cli_obj)

        assert result.exit_code == 0, result.output
        create_engine.assert_called_once_with(build_db_url(db_config))
        assert "Current database revision: abc123" in result.output
        assert "The head revision of available migrations: headrev" in result.output
        engine.dispose.assert_awaited_once()


class _FakeSyncConnection:
    def __init__(self) -> None:
        self.exec_driver_sql = MagicMock()


class _FakeOneshotConnection:
    sync_connection: _FakeSyncConnection
    exec_driver_sql: AsyncMock

    def __init__(self) -> None:
        self.exec_driver_sql = AsyncMock()
        self.sync_connection = _FakeSyncConnection()

    async def run_sync(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        return fn(self.sync_connection, *args, **kwargs)


class _FakeOneshotEngine:
    connection: _FakeOneshotConnection
    sync_engine: MagicMock
    dispose: AsyncMock

    def __init__(self) -> None:
        self.connection = _FakeOneshotConnection()
        self.sync_engine = MagicMock()
        self.dispose = AsyncMock()

    @asynccontextmanager
    async def begin(self) -> AsyncIterator[_FakeOneshotConnection]:
        yield self.connection


class TestSchemaOneshotCommand:
    def test_oneshot_creates_tables_on_a_fresh_database(
        self, workdir: Path, cli_obj: MagicMock, db_config: DatabaseConfig
    ) -> None:
        engine = _FakeOneshotEngine()
        migration_context = MagicMock()
        migration_context.get_current_revision.return_value = None
        script = MagicMock()
        script.get_heads.return_value = ["headrev"]
        with (
            patch(
                "ai.backend.manager.repositories.db.engine.create_async_engine",
                return_value=engine,
            ) as create_engine,
            patch(
                "alembic.runtime.migration.MigrationContext.configure",
                return_value=migration_context,
            ),
            patch("alembic.script.ScriptDirectory.from_config", return_value=script),
            patch("ai.backend.manager.models.base.metadata.create_all") as create_all,
        ):
            result = CliRunner().invoke(schema_cli, ["oneshot"], obj=cli_obj)

        assert result.exit_code == 0, result.output
        create_engine.assert_called_once_with(build_db_url(db_config))
        create_all.assert_called_once_with(engine.sync_engine, checkfirst=False)
        engine.connection.sync_connection.exec_driver_sql.assert_any_call(
            "INSERT INTO alembic_version VALUES('headrev')"
        )
        engine.dispose.assert_awaited_once()

    def test_oneshot_defers_to_upgrade_on_an_existing_database(
        self, workdir: Path, cli_obj: MagicMock, db_config: DatabaseConfig
    ) -> None:
        engine = _FakeOneshotEngine()
        migration_context = MagicMock()
        migration_context.get_current_revision.return_value = "abc123"
        with (
            patch(
                "ai.backend.manager.repositories.db.engine.create_async_engine",
                return_value=engine,
            ) as create_engine,
            patch(
                "alembic.runtime.migration.MigrationContext.configure",
                return_value=migration_context,
            ),
            patch("ai.backend.manager.models.base.metadata.create_all") as create_all,
        ):
            result = CliRunner().invoke(schema_cli, ["oneshot"], obj=cli_obj)

        assert result.exit_code == 0, result.output
        create_engine.assert_called_once_with(build_db_url(db_config))
        create_all.assert_not_called()
        engine.dispose.assert_awaited_once()


_PREVIOUS_VERSION = "24.09.8"


class _FakeRevisionScript:
    def __init__(self, revision: str) -> None:
        self.revision = revision

    @override
    def __str__(self) -> str:
        return self.revision


def _load_revision_history(version: str) -> RevisionHistory:
    with importlib.resources.as_file(
        importlib.resources.files("ai.backend.manager.models.alembic.revision_history")
    ) as f:
        with (f / f"{version}.json").open() as fr:
            history: RevisionHistory = load_json(fr.read())
            return history


class TestSchemaApplyMissingRevisionsCommand:
    @pytest.fixture
    def fake_script_directory(self) -> MagicMock:
        """A ScriptDirectory whose revisions are the previous version's applied history
        plus one pending revision, so the command does not depend on walking the real
        packaged migration scripts."""
        history = _load_revision_history(_PREVIOUS_VERSION)
        applied = [r["revision"] for r in history["revisions"]]
        scripts = [_FakeRevisionScript(r) for r in [*applied, "pending-revision"]]
        script_directory = MagicMock()
        script_directory.walk_revisions.return_value = scripts
        return script_directory

    def test_dry_run_does_not_load_manager_toml(
        self, workdir: Path, cli_obj: MagicMock, fake_script_directory: MagicMock
    ) -> None:
        with patch(
            "alembic.script.ScriptDirectory.from_config", return_value=fake_script_directory
        ):
            result = CliRunner().invoke(
                schema_cli,
                ["apply-missing-revisions", _PREVIOUS_VERSION, "--dry-run"],
                obj=cli_obj,
            )

        assert result.exit_code == 0, result.output
        cli_obj.get_bootstrap_config.assert_not_awaited()
        fake_script_directory.run_env.assert_not_called()

    def test_real_run_resolves_config_from_the_resolver(
        self, workdir: Path, cli_obj: MagicMock, fake_script_directory: MagicMock
    ) -> None:
        with patch(
            "alembic.script.ScriptDirectory.from_config", return_value=fake_script_directory
        ):
            result = CliRunner().invoke(
                schema_cli, ["apply-missing-revisions", _PREVIOUS_VERSION], obj=cli_obj
            )

        assert result.exit_code == 0, result.output
        cli_obj.get_bootstrap_config.assert_awaited()
        fake_script_directory.run_env.assert_called_once()


class TestAgentPingCommand:
    def test_ping_resolves_config_from_the_resolver(
        self, workdir: Path, cli_obj: MagicMock, db_config: DatabaseConfig
    ) -> None:
        engine = _FakeEngine()
        fake_rpc = MagicMock()
        fake_rpc.call.ping = AsyncMock(return_value="pong")

        @asynccontextmanager
        async def _fake_rpc_context(*_args: Any, **_kwargs: Any) -> AsyncIterator[MagicMock]:
            yield fake_rpc

        agent_cache_instance = MagicMock()
        agent_cache_instance.rpc_context = _fake_rpc_context
        with (
            patch("zmq.auth.certs.load_certificate", return_value=(b"pub", b"sec")),
            patch(
                "ai.backend.manager.repositories.db.engine.create_async_engine",
                return_value=engine,
            ) as create_engine,
            patch(
                "ai.backend.manager.agent_cache.AgentRPCCache",
                return_value=agent_cache_instance,
            ) as agent_rpc_cache_cls,
        ):
            result = CliRunner().invoke(agent_cli, ["ping", "agent-id-1"], obj=cli_obj)

        assert result.exit_code == 0, result.output
        create_engine.assert_called_once_with(build_db_url(db_config))
        agent_rpc_cache_cls.assert_called_once()
        engine.dispose.assert_awaited_once()
