from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import shutil
import tempfile
import textwrap
from collections.abc import AsyncIterator, Iterator
from contextlib import AsyncExitStack
from dataclasses import dataclass
from functools import partial, update_wrapper
from pathlib import Path
from typing import Any

import asyncpg
import pytest
import sqlalchemy as sa
import yarl
from aiohttp import web
from pydantic import BaseModel
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
from sqlalchemy.ext.asyncio.engine import create_async_engine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.config import ConfigurationError
from ai.backend.common.jwt.validator import JWTValidator
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.logging import LocalLogger, LogLevel
from ai.backend.logging.config import ConsoleConfig, LogDriver, LoggingConfig
from ai.backend.logging.types import LogFormat
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.cli.context import CLIContext
from ai.backend.manager.cli.dbschema import oneshot as cli_schema_oneshot
from ai.backend.manager.cli.etcd import delete as cli_etcd_delete
from ai.backend.manager.cli.etcd import put_json as cli_etcd_put_json
from ai.backend.manager.config.bootstrap import BootstrapConfig
from ai.backend.manager.models.base import (
    pgsql_connect_opts,
    populate_fixture,
)
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.session_template import session_templates
from ai.backend.manager.models.user import users
from ai.backend.manager.models.vfolder import vfolders
from ai.backend.manager.server import (
    build_root_app,
    config_provider_ctx,
    etcd_ctx,
    global_subapp_pkgs,
    webapp_plugin_ctx,
)
from ai.backend.testutils.bootstrap import (
    etcd_container,
    postgres_container,
    redis_container,
)
from ai.backend.testutils.pants import get_parallel_slot

# Re-export testcontainer fixtures so pytest can discover them
__all__ = [
    "etcd_container",
    "redis_container",
    "postgres_container",
]

here = Path(__file__).parent

log = logging.getLogger("tests.integration.conftest")


@dataclass
class ServerInfo:
    host: str
    port: int

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


def pytest_configure(config: Any) -> None:
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test (requires full-stack server)",
    )


# ---------------------------------------------------------------------------
# Session-scope infrastructure fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def test_id() -> str:
    return secrets.token_hex(12)


@pytest.fixture(scope="session", autouse=True)
def test_ns(test_id: str) -> str:
    ret = f"testing-ns-{test_id}"
    os.environ["BACKEND_NAMESPACE"] = ret
    return ret


@pytest.fixture(scope="session")
def test_db(test_id: str) -> str:
    return f"test_db_{test_id}"


@pytest.fixture(scope="session")
def vfolder_mount(test_id: str) -> Iterator[Path]:
    ret = Path.cwd() / f"tmp/backend.ai/integration-testing/vfolders-{test_id}"
    ret.mkdir(parents=True, exist_ok=True)
    yield ret
    try:
        shutil.rmtree(ret.parent)
    except OSError:
        pass


@pytest.fixture(scope="session")
def vfolder_fsprefix() -> Path:
    return Path("fsprefix/inner/")


@pytest.fixture(scope="session")
def vfolder_host() -> str:
    return "local"


@pytest.fixture(scope="session")
def logging_config() -> Iterator[LoggingConfig]:
    config = LoggingConfig(
        version=1,
        disable_existing_loggers=False,
        handlers={},
        loggers={},
        drivers=[LogDriver.CONSOLE],
        console=ConsoleConfig(
            colored=None,
            format=LogFormat.VERBOSE,
        ),
        file=None,
        logstash=None,
        graylog=None,
        level=LogLevel.DEBUG,
        pkg_ns={
            "": LogLevel.INFO,
            "ai.backend": LogLevel.DEBUG,
            "tests": LogLevel.DEBUG,
            "alembic": LogLevel.INFO,
            "aiotools": LogLevel.INFO,
            "aiohttp": LogLevel.INFO,
            "sqlalchemy": LogLevel.WARNING,
        },
    )
    logger = LocalLogger(config)
    with logger:
        yield config


@pytest.fixture(scope="session")
def ipc_base_path(test_id: str) -> Path:
    ipc_base_path = Path.cwd() / f"tmp/backend.ai/integration-testing/ipc-{test_id}"
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    return ipc_base_path


@pytest.fixture(scope="session")
def bootstrap_config(
    test_id: str,
    ipc_base_path: Path,
    logging_config: LoggingConfig,
    etcd_container: tuple[str, HostPortPairModel],
    redis_container: tuple[str, HostPortPairModel],
    postgres_container: tuple[str, HostPortPairModel],
    test_db: str,
) -> Iterator[BootstrapConfig]:
    etcd_addr = etcd_container[1]
    postgres_addr = postgres_container[1]

    build_root = Path(os.environ["BACKEND_BUILD_ROOT"])

    bootstrap_config = BootstrapConfig.model_validate({
        "etcd": {
            "namespace": test_id,
            "addr": {"host": etcd_addr.host, "port": etcd_addr.port},
        },
        "db": {
            "addr": postgres_addr,
            "name": test_db,
            "user": "postgres",
            "password": "develove",
            "pool-size": 8,
            "pool-recycle": -1,
            "pool-pre-ping": False,
            "max-overflow": 64,
            "lock-conn-timeout": 0,
        },
        "manager": {
            "id": f"i-{test_id}",
            "num-proc": 1,
            "distributed-lock": "filelock",
            "ipc-base-path": ipc_base_path,
            "service-addr": HostPortPairModel(
                host="127.0.0.1", port=29100 + get_parallel_slot() * 10
            ),
            "allowed-plugins": set(),
            "disabled-plugins": set(),
            "rpc-auth-manager-keypair": f"{build_root}/fixtures/manager/manager.key_secret",
        },
        "pyroscope": {
            "enabled": False,
            "app-name": "backend.ai-test",
            "server-addr": "http://localhost:4040",
            "sample-rate": 100,
        },
        "debug": {
            "enabled": False,
            "log-events": False,
            "log-scheduler-ticks": False,
            "periodic-sync-stats": False,
        },
        "logging": logging_config,
    })

    def _override_if_exists(src: BaseModel, dst: BaseModel, key: str) -> None:
        if key in src.model_fields_set:
            setattr(dst, key, getattr(src, key))

    try:
        fs_bootstrap_config = asyncio.run(
            BootstrapConfig.load_from_file(Path("dummy-manager.toml"))
        )
        bootstrap_config.etcd.addr = fs_bootstrap_config.etcd.addr
        _override_if_exists(fs_bootstrap_config.etcd, bootstrap_config.etcd, "user")
        _override_if_exists(fs_bootstrap_config.etcd, bootstrap_config.etcd, "password")
        bootstrap_config.db.addr = fs_bootstrap_config.db.addr
        _override_if_exists(fs_bootstrap_config.db, bootstrap_config.db, "user")
        _override_if_exists(fs_bootstrap_config.db, bootstrap_config.db, "password")
    except (ConfigurationError, FileNotFoundError):
        pass
    yield bootstrap_config
    try:
        shutil.rmtree(ipc_base_path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Session-scope mock context fixtures (for build_root_app argument binding)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def mock_etcd_ctx(
    bootstrap_config: BootstrapConfig,
) -> Any:
    argument_binding_ctx = partial(etcd_ctx, etcd_config=bootstrap_config.etcd.to_dataclass())
    update_wrapper(argument_binding_ctx, etcd_ctx)
    return argument_binding_ctx


@pytest.fixture(scope="session")
def mock_config_provider_ctx(
    bootstrap_config: BootstrapConfig,
) -> Any:
    base_cfg = bootstrap_config.model_dump()
    argument_binding_ctx = partial(
        config_provider_ctx, log_level=LogLevel.DEBUG, config_path=None, extra_config=base_cfg
    )
    update_wrapper(argument_binding_ctx, config_provider_ctx)
    return argument_binding_ctx


# ---------------------------------------------------------------------------
# Session-scope DB / etcd fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def etcd_fixture(
    test_id: str,
    bootstrap_config: BootstrapConfig,
    redis_container: tuple[str, HostPortPairModel],
    vfolder_mount: Path,
    vfolder_fsprefix: Path,
    vfolder_host: str,
) -> Iterator[None]:
    redis_addr = redis_container[1]

    cli_ctx = CLIContext(
        config_path=Path.cwd() / "dummy-manager.toml",
        log_level=LogLevel.DEBUG,
    )
    cli_ctx._bootstrap_config = bootstrap_config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".etcd.json") as f:
        etcd_fixture_data = {
            "manager": {"status": "running"},
            "volumes": {
                "_mount": str(vfolder_mount),
                "_fsprefix": str(vfolder_fsprefix),
                "default_host": str(vfolder_host),
                "proxies": {
                    "local": {
                        "client_api": "http://127.0.0.1:6021",
                        "manager_api": "https://127.0.0.1:6022",
                        "secret": "some-secret-shared-with-storage-proxy",
                        "ssl_verify": "false",
                    }
                },
            },
            "nodes": {},
            "config": {
                "docker": {},
                "redis": {
                    "addr": f"{redis_addr.host}:{redis_addr.port}",
                },
                "plugins": {
                    "cloudia": {
                        "base_url": "127.0.0.1:8090",
                        "user": "fake-cloudia-user@lablup.com",
                        "password": "fake-password",
                    },
                },
            },
        }
        json.dump(etcd_fixture_data, f)
        f.flush()
        click_ctx = cli_etcd_put_json.make_context(
            "test",
            ["", f.name],
            obj=cli_ctx,
        )
        click_ctx.obj = cli_ctx
        cli_etcd_put_json.invoke(click_ctx)
    yield
    click_ctx = cli_etcd_delete.make_context(
        "test",
        ["--prefix", ""],
        obj=cli_ctx,
    )
    cli_etcd_delete.invoke(click_ctx)


@pytest.fixture(scope="session")
def database(request: Any, bootstrap_config: BootstrapConfig, test_db: str) -> None:
    db_url = (
        yarl.URL(f"postgresql+asyncpg://{bootstrap_config.db.addr.host}/testing")
        .with_port(bootstrap_config.db.addr.port)
        .with_user(bootstrap_config.db.user)
    )
    if bootstrap_config.db.password is not None:
        db_url = db_url.with_password(bootstrap_config.db.password)

    async def init_db() -> None:
        engine = create_async_engine(
            str(db_url),
            connect_args=pgsql_connect_opts,
            isolation_level="AUTOCOMMIT",
        )
        while True:
            try:
                async with engine.connect() as conn:
                    await conn.execute(sa.text(f'CREATE DATABASE "{test_db}";'))
            except (asyncpg.exceptions.CannotConnectNowError, ConnectionError):
                await asyncio.sleep(0.1)
                continue
            else:
                break
        await engine.dispose()

    asyncio.run(init_db())

    async def finalize_db() -> None:
        engine = create_async_engine(
            str(db_url),
            connect_args=pgsql_connect_opts,
            isolation_level="AUTOCOMMIT",
        )
        async with engine.connect() as conn:
            await conn.execute(sa.text(f'REVOKE CONNECT ON DATABASE "{test_db}" FROM public;'))
            await conn.execute(
                sa.text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE pid <> pg_backend_pid();"
                )
            )
            await conn.execute(sa.text(f'DROP DATABASE "{test_db}";'))
        await engine.dispose()

    request.addfinalizer(lambda: asyncio.run(finalize_db()))

    alembic_config_template = textwrap.dedent(
        """
    [alembic]
    script_location = ai.backend.manager.models:alembic
    sqlalchemy.url = {sqlalchemy_url:s}

    [loggers]
    keys = root

    [logger_root]
    level = WARNING
    handlers = console

    [handlers]
    keys = console

    [handler_console]
    class = StreamHandler
    args = (sys.stdout,)
    formatter = simple
    level = INFO

    [formatters]
    keys = simple

    [formatter_simple]
    format = [%(name)s] %(message)s
    """
    ).strip()

    cli_ctx = CLIContext(
        config_path=Path.cwd() / "dummy-manager.toml",
        log_level=LogLevel.DEBUG,
    )
    cli_ctx._bootstrap_config = bootstrap_config
    test_db_url = db_url.with_path(test_db)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf8") as alembic_cfg:
        alembic_cfg_data = alembic_config_template.format(
            sqlalchemy_url=str(test_db_url),
        )
        alembic_cfg.write(alembic_cfg_data)
        alembic_cfg.flush()
        click_ctx = cli_schema_oneshot.make_context(
            "test",
            ["-f", alembic_cfg.name],
            obj=cli_ctx,
        )
        cli_schema_oneshot.invoke(click_ctx)


# ---------------------------------------------------------------------------
# Function-scope fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def database_fixture(
    bootstrap_config: BootstrapConfig, test_db: str, database: None
) -> AsyncIterator[None]:
    """Populate example fixture data into the database, then clean up after each test."""
    db_url = (
        yarl.URL(f"postgresql+asyncpg://{bootstrap_config.db.addr.host}/{test_db}")
        .with_port(bootstrap_config.db.addr.port)
        .with_user(bootstrap_config.db.user)
    )
    if bootstrap_config.db.password is not None:
        db_url = db_url.with_password(bootstrap_config.db.password)

    build_root = Path(os.environ["BACKEND_BUILD_ROOT"])

    fixture_paths = [
        build_root / "fixtures" / "manager" / "example-users.json",
        build_root / "fixtures" / "manager" / "example-keypairs.json",
        build_root / "fixtures" / "manager" / "example-set-user-main-access-keys.json",
        build_root / "fixtures" / "manager" / "example-resource-presets.json",
        build_root / "fixtures" / "manager" / "example-container-registries-harbor.json",
    ]

    async def init_fixture() -> None:
        engine: SAEngine = create_async_engine(
            str(db_url),
            connect_args=pgsql_connect_opts,
        )
        try:
            for fixture_path in fixture_paths:
                with open(fixture_path, "rb") as fp:
                    data = json.load(fp)
                try:
                    await populate_fixture(engine, data)
                except ValueError:
                    log.error("Failed to populate fixtures from %s", fixture_path)
                    raise
        finally:
            await engine.dispose()

    await init_fixture()

    yield

    async def clean_fixture() -> None:
        engine: SAEngine = create_async_engine(
            str(db_url),
            connect_args=pgsql_connect_opts,
        )
        try:
            async with engine.begin() as conn:
                await conn.execute(vfolders.delete())
                await conn.execute(kernels.delete())
                await conn.execute(SessionRow.__table__.delete())
                await conn.execute(session_templates.delete())
                await conn.execute(keypairs.delete())
                await conn.execute(users.delete())
                await conn.execute(domains.delete())
                await conn.execute(ImageAliasRow.__table__.delete())
                await conn.execute(ImageRow.__table__.delete())
        finally:
            await engine.dispose()

    await clean_fixture()


@pytest.fixture()
async def server_factory(
    bootstrap_config: BootstrapConfig,
    database_fixture: None,
    etcd_fixture: None,
) -> AsyncIterator[ServerInfo]:
    """
    Start a full-stack manager server with ALL cleanup_contexts.

    This is the key difference from component tests:
    - Component tests use selective cleanup_contexts (or an empty list)
    - Integration tests use cleanup_contexts=None (ALL cleanup_contexts)

    The server lifecycle follows the same pattern as ``server_main()`` in
    ``ai.backend.manager.server``:
    1. Build the root app with ALL cleanup_contexts and subapp packages
    2. Initialize etcd_ctx and config_provider_ctx separately
    3. Initialize webapp_plugin_ctx for plugin webapp loading
    4. Start the server with AppRunner + TCPSite
    """
    init_stack = AsyncExitStack()

    root_app = build_root_app(
        0,
        bootstrap_config,
        cleanup_contexts=None,
        subapp_pkgs=global_subapp_pkgs,
    )
    root_ctx: RootContext = root_app["_root.context"]

    await init_stack.__aenter__()
    try:
        await init_stack.enter_async_context(
            etcd_ctx(root_ctx, bootstrap_config.etcd.to_dataclass())
        )
        base_cfg = bootstrap_config.model_dump()
        await init_stack.enter_async_context(
            config_provider_ctx(root_ctx, LogLevel.DEBUG, config_path=None, extra_config=base_cfg)
        )

        jwt_config = root_ctx.config_provider.config.jwt.to_jwt_config()
        root_ctx.jwt_validator = JWTValidator(jwt_config)

        await init_stack.enter_async_context(webapp_plugin_ctx(root_app))

        runner = web.AppRunner(root_app, handle_signals=False)
        await runner.setup()

        service_addr = root_ctx.config_provider.config.manager.service_addr
        site = web.TCPSite(
            runner,
            service_addr.host,
            service_addr.port,
            reuse_port=True,
        )
        await site.start()

        yield ServerInfo(host=str(service_addr.host), port=service_addr.port)
    finally:
        await runner.cleanup()
        await init_stack.__aexit__(None, None, None)


@pytest.fixture()
async def admin_registry(server_factory: ServerInfo) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry with superadmin keypair."""
    config = ClientConfig(endpoint=yarl.URL(server_factory.url))
    auth = HMACAuth(
        access_key="AKIAIOSFODNN7EXAMPLE",
        secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    )
    registry = await BackendAIClientRegistry.create(config, auth)
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def user_registry(server_factory: ServerInfo) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry with normal-user keypair."""
    config = ClientConfig(endpoint=yarl.URL(server_factory.url))
    auth = HMACAuth(
        access_key="AKIANABBDUSEREXAMPLE",
        secret_key="C8qnIo29EZvXkPK_MXcuAakYTy4NYrxwmCEyNPlf",
    )
    registry = await BackendAIClientRegistry.create(config, auth)
    try:
        yield registry
    finally:
        await registry.close()
