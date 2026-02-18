from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import shutil
import tempfile
import textwrap
import uuid
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import AbstractAsyncContextManager, AsyncExitStack
from dataclasses import dataclass
from functools import partial, update_wrapper
from pathlib import Path

import asyncpg
import pytest
import sqlalchemy as sa
import yarl
from aiohttp import web
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
from sqlalchemy.ext.asyncio.engine import create_async_engine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
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
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.base import pgsql_connect_opts
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import association_groups_users
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
    keypair_resource_policies,
)
from ai.backend.manager.models.scaling_group import scaling_groups, sgroups_for_domains
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.session_template import session_templates
from ai.backend.manager.models.user import users
from ai.backend.manager.models.vfolder import vfolders
from ai.backend.manager.server import (
    build_root_app,
    config_provider_ctx,
    etcd_ctx,
    global_subapp_pkgs,
)
from ai.backend.testutils.bootstrap import (  # noqa: F401
    etcd_container,
    postgres_container,
    redis_container,
)
from ai.backend.testutils.pants import get_parallel_slot

log = logging.getLogger("tests.component.conftest")


@dataclass
class ServerInfo:
    host: str
    port: int

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


# ---------------------------------------------------------------------------
# Session-scoped infrastructure fixtures
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
    ret = Path.cwd() / f"tmp/backend.ai/component-testing/vfolders-{test_id}"
    ret.mkdir(parents=True, exist_ok=True)
    yield ret
    try:
        shutil.rmtree(ret.parent)
    except OSError:
        pass


@pytest.fixture(scope="session")
def vfolder_fsprefix() -> Path:
    # NOTE: the prefix must NOT start with "/"
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
    ipc_base_path = Path.cwd() / f"tmp/backend.ai/component-testing/ipc-{test_id}"
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    return ipc_base_path


@pytest.fixture(scope="session")
def bootstrap_config(
    test_id: str,
    ipc_base_path: Path,
    logging_config: LoggingConfig,
    etcd_container: tuple[str, HostPortPairModel],  # noqa: F811
    redis_container: tuple[str, HostPortPairModel],  # noqa: F811
    postgres_container: tuple[str, HostPortPairModel],  # noqa: F811
    test_db: str,
) -> Iterator[BootstrapConfig]:
    etcd_addr = etcd_container[1]
    postgres_addr = postgres_container[1]

    build_root = Path(os.environ["BACKEND_BUILD_ROOT"])

    config = BootstrapConfig.model_validate({
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

    yield config
    try:
        shutil.rmtree(ipc_base_path)
    except OSError:
        pass


EtcdCtxFactory = Callable[[RootContext], AbstractAsyncContextManager[None]]
ConfigProviderCtxFactory = Callable[
    [RootContext], AbstractAsyncContextManager[ManagerConfigProvider]
]


@pytest.fixture(scope="session")
def mock_etcd_ctx(
    bootstrap_config: BootstrapConfig,
) -> EtcdCtxFactory:
    argument_binding_ctx = partial(etcd_ctx, etcd_config=bootstrap_config.etcd.to_dataclass())
    update_wrapper(argument_binding_ctx, etcd_ctx)
    return argument_binding_ctx


@pytest.fixture(scope="session")
def mock_config_provider_ctx(
    bootstrap_config: BootstrapConfig,
) -> ConfigProviderCtxFactory:
    base_cfg = bootstrap_config.model_dump()
    argument_binding_ctx = partial(
        config_provider_ctx, log_level=LogLevel.DEBUG, config_path=None, extra_config=base_cfg
    )
    update_wrapper(argument_binding_ctx, config_provider_ctx)
    return argument_binding_ctx


@pytest.fixture(scope="session")
def etcd_fixture(
    test_id: str,
    bootstrap_config: BootstrapConfig,
    redis_container: tuple[str, HostPortPairModel],  # noqa: F811
    vfolder_mount: Path,
    vfolder_fsprefix: Path,
    vfolder_host: str,
) -> Iterator[None]:
    redis_addr = redis_container[1]

    cli_ctx = CLIContext(log_level=LogLevel.DEBUG)
    cli_ctx._bootstrap_config = bootstrap_config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".etcd.json") as f:
        etcd_data = {
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
        json.dump(etcd_data, f)
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
def database(
    request: pytest.FixtureRequest, bootstrap_config: BootstrapConfig, test_db: str
) -> None:
    """
    Create a new database for the current test session
    and install the table schema using alembic.
    """
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

    cli_ctx = CLIContext(log_level=LogLevel.DEBUG)
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
# Function-scoped per-test fixtures
# ---------------------------------------------------------------------------


ADMIN_USER_UUID = uuid.UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")
ADMIN_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
ADMIN_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

USER_UUID = uuid.UUID("dfa9da54-4b28-432f-be29-c0d680c7a412")
USER_ACCESS_KEY = "AKIANABBDUSEREXAMPLE"
USER_SECRET_KEY = "C8qnIo29EZvXkPK_MXcuAakYTy4NYrxwmCEyNPlf"

DEFAULT_GROUP_UUID = uuid.UUID("2de2b969-1d04-48a6-af16-0bc8adb3c831")


@pytest.fixture()
async def database_fixture(
    bootstrap_config: BootstrapConfig,
    test_db: str,
    database: None,
) -> AsyncIterator[None]:
    """Populate minimal fixture data programmatically via SQLAlchemy insert."""
    db_url = (
        yarl.URL(f"postgresql+asyncpg://{bootstrap_config.db.addr.host}/{test_db}")
        .with_port(bootstrap_config.db.addr.port)
        .with_user(bootstrap_config.db.user)
    )
    if bootstrap_config.db.password is not None:
        db_url = db_url.with_password(bootstrap_config.db.password)

    engine: SAEngine = create_async_engine(
        str(db_url),
        connect_args=pgsql_connect_opts,
    )
    try:
        async with engine.begin() as conn:
            # 1) domains
            await conn.execute(
                sa.insert(domains).values(
                    name="default",
                    description="The default domain",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                )
            )
            # 2) resource policies (user, project, keypair)
            await conn.execute(
                sa.insert(UserResourcePolicyRow.__table__).values(
                    name="default",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=3,
                )
            )
            await conn.execute(
                sa.insert(ProjectResourcePolicyRow.__table__).values(
                    name="default",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            await conn.execute(
                sa.insert(keypair_resource_policies).values(
                    name="default",
                    default_for_unspecified="UNLIMITED",
                    total_resource_slots={},
                    max_session_lifetime=0,
                    max_concurrent_sessions=5,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                    allowed_vfolder_hosts={},
                )
            )
            # 3) scaling group + domain association
            await conn.execute(
                sa.insert(scaling_groups).values(
                    name="default",
                    description="The default agent scaling group",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts={},
                )
            )
            await conn.execute(
                sa.insert(sgroups_for_domains).values(
                    scaling_group="default",
                    domain="default",
                )
            )
            # 4) groups (projects) — use sa.table() to bypass ORM column defaults
            await conn.execute(
                sa.insert(
                    sa.table(
                        "groups",
                        sa.column("id"),
                        sa.column("name"),
                        sa.column("description"),
                        sa.column("is_active"),
                        sa.column("domain_name"),
                        sa.column("resource_policy"),
                        sa.column("total_resource_slots"),
                        sa.column("allowed_vfolder_hosts"),
                        sa.column("type"),
                    )
                ).values(
                    id=str(DEFAULT_GROUP_UUID),
                    name="default",
                    description="The default user group",
                    is_active=True,
                    domain_name="default",
                    resource_policy="default",
                    total_resource_slots="{}",
                    allowed_vfolder_hosts="{}",
                    type="general",
                )
            )
            # 5) users (admin + normal user)
            await conn.execute(
                sa.insert(users).values([
                    {
                        "uuid": str(ADMIN_USER_UUID),
                        "username": "admin",
                        "email": "admin@lablup.com",
                        "password": "wJalrXUt",
                        "need_password_change": False,
                        "full_name": "Admin Lablup",
                        "description": "Lablup's Admin Account",
                        "status": "active",
                        "status_info": "admin-requested",
                        "domain_name": "default",
                        "resource_policy": "default",
                        "role": "superadmin",
                    },
                    {
                        "uuid": str(USER_UUID),
                        "username": "user",
                        "email": "user@lablup.com",
                        "password": "C8qnIo29",
                        "need_password_change": False,
                        "full_name": "User Lablup",
                        "description": "Lablup's User Account",
                        "status": "active",
                        "status_info": "admin-requested",
                        "domain_name": "default",
                        "resource_policy": "default",
                        "role": "user",
                    },
                ])
            )
            # 6) keypairs
            await conn.execute(
                sa.insert(keypairs).values([
                    {
                        "user_id": "admin@lablup.com",
                        "access_key": ADMIN_ACCESS_KEY,
                        "secret_key": ADMIN_SECRET_KEY,
                        "is_active": True,
                        "resource_policy": "default",
                        "rate_limit": 30000,
                        "num_queries": 0,
                        "is_admin": True,
                        "user": str(ADMIN_USER_UUID),
                    },
                    {
                        "user_id": "user@lablup.com",
                        "access_key": USER_ACCESS_KEY,
                        "secret_key": USER_SECRET_KEY,
                        "is_active": True,
                        "resource_policy": "default",
                        "rate_limit": 30000,
                        "num_queries": 0,
                        "is_admin": False,
                        "user": str(USER_UUID),
                    },
                ])
            )
            # 7) association_groups_users
            await conn.execute(
                sa.insert(association_groups_users).values([
                    {
                        "group_id": str(DEFAULT_GROUP_UUID),
                        "user_id": str(ADMIN_USER_UUID),
                    },
                    {
                        "group_id": str(DEFAULT_GROUP_UUID),
                        "user_id": str(USER_UUID),
                    },
                ])
            )
    finally:
        await engine.dispose()

    yield

    # Cleanup: delete rows inserted above (reverse FK order)
    engine = create_async_engine(
        str(db_url),
        connect_args=pgsql_connect_opts,
    )
    try:
        async with engine.begin() as conn:
            await conn.execute(vfolders.delete())
            await conn.execute(kernels.delete())
            await conn.execute(SessionRow.__table__.delete())
            await conn.execute(session_templates.delete())
            await conn.execute(association_groups_users.delete())
            await conn.execute(keypairs.delete())
            await conn.execute(users.delete())
            await conn.execute(sgroups_for_domains.delete())
            await conn.execute(scaling_groups.delete())
            await conn.execute(sa.text("DELETE FROM groups"))
            await conn.execute(domains.delete())
            await conn.execute(keypair_resource_policies.delete())
            await conn.execute(UserResourcePolicyRow.__table__.delete())
            await conn.execute(ProjectResourcePolicyRow.__table__.delete())
            await conn.execute(ImageAliasRow.__table__.delete())
            await conn.execute(ImageRow.__table__.delete())
    finally:
        await engine.dispose()


@pytest.fixture()
async def server(
    bootstrap_config: BootstrapConfig,
    mock_etcd_ctx: EtcdCtxFactory,
    mock_config_provider_ctx: ConfigProviderCtxFactory,
    etcd_fixture: None,
    database_fixture: None,
) -> AsyncIterator[ServerInfo]:
    """
    Start a full manager server and return its connection info.

    This is the only fixture that depends on server internals
    (build_root_app, cleanup_contexts). When Handler-based migration
    happens, only this fixture's implementation changes.
    """
    app = build_root_app(
        0,
        bootstrap_config,
        cleanup_contexts=None,
        subapp_pkgs=list(global_subapp_pkgs),
    )
    root_ctx: RootContext = app["_root.context"]

    exit_stack = AsyncExitStack()
    await exit_stack.__aenter__()

    # Pre-initialize etcd and config_provider contexts
    # (matching production server_main() at L1820-1828)
    await exit_stack.enter_async_context(mock_etcd_ctx(root_ctx))
    await exit_stack.enter_async_context(mock_config_provider_ctx(root_ctx))

    runner = web.AppRunner(app, handle_signals=False)
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

    await runner.cleanup()
    await exit_stack.aclose()


@pytest.fixture()
async def admin_registry(server: ServerInfo) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry with superadmin keypair."""
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(access_key=ADMIN_ACCESS_KEY, secret_key=ADMIN_SECRET_KEY),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def user_registry(server: ServerInfo) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry with normal-user keypair."""
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(access_key=USER_ACCESS_KEY, secret_key=USER_SECRET_KEY),
    )
    try:
        yield registry
    finally:
        await registry.close()
