from __future__ import annotations

import asyncio
import enum
import hashlib
import hmac
import json
import logging
import os
import secrets
import shutil
import tempfile
import textwrap
import uuid
from datetime import datetime
from decimal import Decimal
from functools import partial, update_wrapper
from pathlib import Path
from typing import (
    Any,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
)
from unittest.mock import AsyncMock, MagicMock

import aiofiles.os
import aiohttp
import asyncpg
import pytest
import sqlalchemy as sa
import yarl
from aiohttp import web
from dateutil.tz import tzutc
from pydantic import BaseModel
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
from sqlalchemy.ext.asyncio.engine import create_async_engine

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.config import ConfigurationError
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.lock import FileLock
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ResourceSlot
from ai.backend.logging import LocalLogger, LogLevel
from ai.backend.logging.config import ConsoleConfig, LogDriver, LoggingConfig
from ai.backend.logging.types import LogFormat
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.cli.context import CLIContext
from ai.backend.manager.cli.dbschema import oneshot as cli_schema_oneshot
from ai.backend.manager.cli.etcd import delete as cli_etcd_delete
from ai.backend.manager.cli.etcd import put_json as cli_etcd_put_json
from ai.backend.manager.config.bootstrap import BootstrapConfig
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models import (
    DomainRow,
    GroupRow,
    ImageRow,
    KernelRow,
    ProjectResourcePolicyRow,
    ScalingGroupRow,
    SessionRow,
    UserResourcePolicyRow,
    UserRow,
    agents,
    domains,
    kernels,
    keypairs,
    scaling_groups,
    users,
    vfolders,
)
from ai.backend.manager.models.base import (
    pgsql_connect_opts,
    populate_fixture,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageAliasRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.models.session_template import session_templates
from ai.backend.manager.models.utils import connect_database
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.server import build_root_app, config_provider_ctx, etcd_ctx
from ai.backend.testutils.bootstrap import (  # noqa: F401
    etcd_container,
    postgres_container,
    redis_container,
)
from ai.backend.testutils.pants import get_parallel_slot


def create_test_password_info(password: str = "test_password") -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


here = Path(__file__).parent

log = logging.getLogger("tests.manager.conftest")


def pytest_addoption(parser):
    parser.addoption(
        "--rescan-cr-backend-ai",
        action="store_true",
        default=False,
        help="Enable tests marked as rescan_cr_backend_ai",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "rescan_cr_backend_ai: mark test to run only when --rescan-cr-backend-ai is set",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--rescan-cr-backend-ai"):
        skip_flag = pytest.mark.skip(reason="--rescan-cr-backend-ai not set")
        for item in items:
            if "rescan_cr_backend_ai" in item.keywords:
                item.add_marker(skip_flag)


@pytest.fixture(scope="session", autouse=True)
def test_id():
    return secrets.token_hex(12)


@pytest.fixture(scope="session", autouse=True)
def test_ns(test_id):
    ret = f"testing-ns-{test_id}"
    os.environ["BACKEND_NAMESPACE"] = ret
    return ret


@pytest.fixture(scope="session")
def test_db(test_id):
    return f"test_db_{test_id}"


@pytest.fixture(scope="session")
def vfolder_mount(test_id):
    ret = Path.cwd() / f"tmp/backend.ai/manager-testing/vfolders-{test_id}"
    ret.mkdir(parents=True, exist_ok=True)
    yield ret
    try:
        shutil.rmtree(ret.parent)
    except IOError:
        pass


@pytest.fixture(scope="session")
def vfolder_fsprefix(test_id):
    # NOTE: the prefix must NOT start with "/"
    return Path("fsprefix/inner/")


@pytest.fixture(scope="session")
def vfolder_host():
    return "local"


@pytest.fixture(scope="session")
def logging_config():
    config = LoggingConfig(
        drivers=[LogDriver.CONSOLE],
        console=ConsoleConfig(
            colored=None,
            format=LogFormat.VERBOSE,
        ),
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
def ipc_base_path(test_id) -> Path:
    ipc_base_path = Path.cwd() / f"tmp/backend.ai/manager-testing/ipc-{test_id}"
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    return ipc_base_path


@pytest.fixture(scope="session")
def bootstrap_config(
    test_id,
    ipc_base_path: Path,
    logging_config,
    etcd_container,  # noqa: F811
    redis_container,  # noqa: F811
    postgres_container,  # noqa: F811
    test_db,
) -> Iterator[BootstrapConfig]:
    etcd_addr = etcd_container[1]
    postgres_addr = postgres_container[1]

    build_root = Path(os.environ["BACKEND_BUILD_ROOT"])

    # Establish a self-contained config.
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
        # Override external database config with the current environment's config.
        fs_boostrap_config = asyncio.run(BootstrapConfig.load_from_file(Path("dummy-manager.toml")))
        bootstrap_config.etcd.addr = fs_boostrap_config.etcd.addr
        _override_if_exists(fs_boostrap_config.etcd, bootstrap_config.etcd, "user")
        _override_if_exists(fs_boostrap_config.etcd, bootstrap_config.etcd, "password")
        bootstrap_config.db.addr = fs_boostrap_config.db.addr
        _override_if_exists(fs_boostrap_config.db, bootstrap_config.db, "user")
        _override_if_exists(fs_boostrap_config.db, bootstrap_config.db, "password")
    except ConfigurationError:
        pass
    yield bootstrap_config
    try:
        shutil.rmtree(ipc_base_path)
    except IOError:
        pass


@pytest.fixture(scope="session")
def mock_etcd_ctx(
    bootstrap_config: BootstrapConfig,
) -> Any:
    argument_binding_ctx = partial(etcd_ctx, etcd_config=bootstrap_config.etcd.to_dataclass())
    update_wrapper(argument_binding_ctx, etcd_ctx)
    return argument_binding_ctx


@pytest.fixture
def event_dispatcher_test_ctx():
    # TODO: Remove this fixture when the root context is refactored
    from contextlib import asynccontextmanager as actxmgr

    @actxmgr
    async def event_dispatcher_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
        root_ctx.event_dispatcher = EventDispatcher(
            root_ctx.message_queue,
            log_events=root_ctx.config_provider.config.debug.log_events,
            event_observer=root_ctx.metrics.event,
        )
        await root_ctx.event_dispatcher.start()
        yield
        await root_ctx.event_dispatcher.close()

    return event_dispatcher_ctx


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


@pytest.fixture(scope="session")
def etcd_fixture(
    test_id,
    bootstrap_config,
    redis_container,  # noqa: F811
    vfolder_mount,
    vfolder_fsprefix,
    vfolder_host,
) -> Iterator[None]:
    # Clear and reset etcd namespace using CLI functions.
    redis_addr = redis_container[1]

    cli_ctx = CLIContext(
        config_path=Path.cwd() / "dummy-manager.toml",
        log_level=LogLevel.DEBUG,
    )
    cli_ctx._bootstrap_config = bootstrap_config  # override the lazy-loaded config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".etcd.json") as f:
        etcd_fixture = {
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
        json.dump(etcd_fixture, f)
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


@pytest.fixture
def local_config(bootstrap_config: BootstrapConfig) -> dict[str, Any]:
    """
    Provide a local_config fixture that returns the bootstrap config as a dictionary.
    This is used by session processors and other components that expect config in dict format.
    """
    config_dict = bootstrap_config.model_dump()

    # Convert back to proper types for compatibility with AsyncEtcd
    from ai.backend.common.typed_validators import HostPortPair

    config_dict["etcd"]["addr"] = HostPortPair(
        host=config_dict["etcd"]["addr"]["host"], port=config_dict["etcd"]["addr"]["port"]
    )

    return config_dict


@pytest.fixture
async def unified_config(
    app, bootstrap_config: BootstrapConfig, etcd_fixture
) -> AsyncIterator[ManagerUnifiedConfig]:
    root_ctx: RootContext = app["_root.context"]
    etcd = AsyncEtcd.initialize(bootstrap_config.etcd.to_dataclass())
    root_ctx.etcd = etcd
    etcd_loader = LegacyEtcdLoader(root_ctx.etcd)
    raw_config = await etcd_loader.load()
    merged_config = {**bootstrap_config.model_dump(), **raw_config}
    unified_config = ManagerUnifiedConfig(**merged_config)
    yield unified_config


@pytest.fixture(scope="session")
def database(request, bootstrap_config: BootstrapConfig, test_db: str) -> None:
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
                # Workaround intermittent test failures in GitHub Actions
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

    # Load the database schema using CLI function.
    cli_ctx = CLIContext(
        config_path=Path.cwd() / "dummy-manager.toml",
        log_level=LogLevel.DEBUG,
    )
    cli_ctx._bootstrap_config = bootstrap_config  # override the lazy-loaded config
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


# Deprecated: Use `database_connection` from tests/conftest.py with `with_tables` instead.
# This fixture creates full schema via Alembic which is slow for simple repository tests.
@pytest.fixture()
async def database_engine(bootstrap_config, database):
    async with connect_database(bootstrap_config.db) as db:
        yield db


@pytest.fixture()
def extra_fixtures():
    return {}


@pytest.fixture()
async def database_fixture(
    bootstrap_config, test_db, database, extra_fixtures
) -> AsyncIterator[None]:
    """
    Populate the example data as fixtures to the database
    and delete them after use.
    """
    db_url = (
        yarl.URL(f"postgresql+asyncpg://{bootstrap_config.db.addr.host}/{test_db}")
        .with_port(bootstrap_config.db.addr.port)
        .with_user(bootstrap_config.db.user)
    )
    if bootstrap_config.db.password is not None:
        db_url = db_url.with_password(bootstrap_config.db.password)

    build_root = Path(os.environ["BACKEND_BUILD_ROOT"])

    extra_fixture_file = tempfile.NamedTemporaryFile(delete=False)
    extra_fixture_file_path = Path(extra_fixture_file.name)

    def fixture_json_encoder(obj: Any):
        if isinstance(obj, ResourceSlot):
            return obj.to_json()
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return str(obj)
        if isinstance(obj, enum.Enum) or isinstance(obj, enum.StrEnum):
            return obj.value
        if isinstance(obj, yarl.URL):
            return str(obj)
        if isinstance(obj, Mapping):
            return dict(obj)

        raise TypeError(f'Fixture type "{type(obj)}" not serializable')

    with open(extra_fixture_file_path, "w") as f:
        json.dump(extra_fixtures, f, default=fixture_json_encoder)

    fixture_paths = [
        build_root / "fixtures" / "manager" / "example-users.json",
        build_root / "fixtures" / "manager" / "example-keypairs.json",
        build_root / "fixtures" / "manager" / "example-set-user-main-access-keys.json",
        build_root / "fixtures" / "manager" / "example-resource-presets.json",
        build_root / "fixtures" / "manager" / "example-container-registries-harbor.json",
        extra_fixture_file_path,
    ]

    async def init_fixture() -> None:
        engine: SAEngine = create_async_engine(
            str(db_url),
            connect_args=pgsql_connect_opts,
        )
        try:
            for fixture_path in fixture_paths:
                with open(fixture_path, "rb") as f:
                    data = json.load(f)
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
        if extra_fixture_file_path.exists():
            await aiofiles.os.remove(extra_fixture_file_path)

        engine: SAEngine = create_async_engine(
            str(db_url),
            connect_args=pgsql_connect_opts,
        )
        try:
            async with engine.begin() as conn:
                await conn.execute((vfolders.delete()))
                await conn.execute((kernels.delete()))
                await conn.execute((SessionRow.__table__.delete()))
                await conn.execute((agents.delete()))
                await conn.execute((session_templates.delete()))
                await conn.execute((keypairs.delete()))
                await conn.execute((users.delete()))
                await conn.execute((scaling_groups.delete()))
                await conn.execute((domains.delete()))
                await conn.execute((ImageAliasRow.__table__.delete()))
                await conn.execute((ImageRow.__table__.delete()))
                await conn.execute((ContainerRegistryRow.__table__.delete()))
        finally:
            await engine.dispose()

    await clean_fixture()


@pytest.fixture
def file_lock_factory(
    ipc_base_path: Path,
    request: pytest.FixtureRequest,
) -> Callable[[str], FileLock]:
    def _make_lock(lock_id: str) -> FileLock:
        lock_path = ipc_base_path / f"testing.{lock_id}.lock"
        lock = FileLock(lock_path, timeout=0)
        request.addfinalizer(partial(lock_path.unlink, missing_ok=True))
        return lock

    return _make_lock


class Client:
    def __init__(self, session: aiohttp.ClientSession, url) -> None:
        self._session = session
        if not url.endswith("/"):
            url += "/"
        self._url = url

    def request(self, method, path, **kwargs):
        while path.startswith("/"):
            path = path[1:]
        url = self._url + path
        return self._session.request(method, url, **kwargs)

    def get(self, path, **kwargs):
        while path.startswith("/"):
            path = path[1:]
        url = self._url + path
        return self._session.get(url, **kwargs)

    def post(self, path, **kwargs):
        while path.startswith("/"):
            path = path[1:]
        url = self._url + path
        return self._session.post(url, **kwargs)

    def put(self, path, **kwargs):
        while path.startswith("/"):
            path = path[1:]
        url = self._url + path
        return self._session.put(url, **kwargs)

    def patch(self, path, **kwargs):
        while path.startswith("/"):
            path = path[1:]
        url = self._url + path
        return self._session.patch(url, **kwargs)

    def delete(self, path, **kwargs):
        while path.startswith("/"):
            path = path[1:]
        url = self._url + path
        return self._session.delete(url, **kwargs)

    def ws_connect(self, path, **kwargs):
        while path.startswith("/"):
            path = path[1:]
        url = self._url + path
        return self._session.ws_connect(url, **kwargs)


@pytest.fixture
async def app(bootstrap_config):
    """
    Create an empty application with the test configuration.
    """
    return build_root_app(
        0,
        bootstrap_config,
        cleanup_contexts=[],
        subapp_pkgs=[],
    )


@pytest.fixture
async def create_app_and_client(bootstrap_config) -> AsyncIterator:
    client: Client | None = None
    client_session: aiohttp.ClientSession | None = None
    runner: web.BaseRunner | None = None
    _outer_ctxs: List[AsyncContextManager] = []

    async def app_builder(
        cleanup_contexts: Optional[Sequence[CleanupContext]] = None,
        subapp_pkgs: Optional[Sequence[str]] = None,
        scheduler_opts: Optional[Mapping[str, Any]] = None,
    ) -> Tuple[web.Application, Client]:
        nonlocal client, client_session, runner
        nonlocal _outer_ctxs

        if scheduler_opts is None:
            scheduler_opts = {}
        _cleanup_ctxs = []
        _outer_ctx_classes: List[Type[AsyncContextManager]] = []
        if cleanup_contexts is not None:
            for ctx in cleanup_contexts:
                # if isinstance(ctx, AsyncContextManager):
                if ctx.__name__ in ["webapp_plugins_ctx"]:
                    _outer_ctx_classes.append(ctx)  # type: ignore
                else:
                    _cleanup_ctxs.append(ctx)
        app = build_root_app(
            0,
            bootstrap_config,
            cleanup_contexts=_cleanup_ctxs,
            subapp_pkgs=subapp_pkgs,
            scheduler_opts={
                "close_timeout": 10,
                **scheduler_opts,
            },
        )
        root_ctx: RootContext = app["_root.context"]
        for octx_cls in _outer_ctx_classes:
            octx = octx_cls(root_ctx)  # type: ignore
            _outer_ctxs.append(octx)
            await octx.__aenter__()
        runner = web.AppRunner(app, handle_signals=False)
        await runner.setup()
        site = web.TCPSite(
            runner,
            root_ctx.config_provider.config.manager.service_addr.host,
            root_ctx.config_provider.config.manager.service_addr.port,
            reuse_port=True,
        )
        await site.start()
        port = root_ctx.config_provider.config.manager.service_addr.port
        client_session = aiohttp.ClientSession()
        client = Client(client_session, f"http://127.0.0.1:{port}")
        return app, client

    yield app_builder

    if client_session is not None:
        await client_session.close()
    if runner is not None:
        await runner.cleanup()
    for octx in reversed(_outer_ctxs):
        await octx.__aexit__(None, None, None)


@pytest.fixture
def default_keypair():
    return {
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    }


@pytest.fixture
def default_domain_keypair():
    """Default domain admin keypair"""
    return {
        "access_key": "AKIAHUKCHDEZGEXAMPLE",
        "secret_key": "cWbsM_vBB4CzTW7JdORRMx8SjGI3-wEXAMPLEKEY",
    }


@pytest.fixture
def user_keypair():
    return {
        "access_key": "AKIANABBDUSEREXAMPLE",
        "secret_key": "C8qnIo29EZvXkPK_MXcuAakYTy4NYrxwmCEyNPlf",
    }


@pytest.fixture
def monitor_keypair():
    return {
        "access_key": "AKIANAMONITOREXAMPLE",
        "secret_key": "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",
    }


@pytest.fixture
def get_headers(app, default_keypair, bootstrap_config):
    def create_header(
        method,
        url,
        req_bytes,
        allowed_ip="10.10.10.10",  # Same with fixture
        ctype="application/json",
        hash_type="sha256",
        api_version="v5.20191215",
        keypair=default_keypair,
    ) -> dict[str, str]:
        now = datetime.now(tzutc())
        hostname = f"127.0.0.1:{bootstrap_config.manager.service_addr.port}"
        headers = {
            "Date": now.isoformat(),
            "Content-Type": ctype,
            "Content-Length": str(len(req_bytes)),
            "X-BackendAI-Version": api_version,
            "X-Forwarded-For": allowed_ip,
        }
        if api_version >= "v4.20181215":
            req_bytes = b""
        else:
            if ctype.startswith("multipart"):
                req_bytes = b""
        if ctype.startswith("multipart"):
            # Let aiohttp to create appropriate header values
            # (e.g., multipart content-type header with message boundaries)
            del headers["Content-Type"]
            del headers["Content-Length"]
        req_hash = hashlib.new(hash_type, req_bytes).hexdigest()
        sign_bytes = (
            method.upper().encode()
            + b"\n"
            + url.encode()
            + b"\n"
            + now.isoformat().encode()
            + b"\n"
            + b"host:"
            + hostname.encode()
            + b"\n"
            + b"content-type:"
            + ctype.encode()
            + b"\n"
            + b"x-backendai-version:"
            + api_version.encode()
            + b"\n"
            + req_hash.encode()
        )
        sign_key = hmac.new(
            keypair["secret_key"].encode(), now.strftime("%Y%m%d").encode(), hash_type
        ).digest()
        sign_key = hmac.new(sign_key, hostname.encode(), hash_type).digest()
        signature = hmac.new(sign_key, sign_bytes, hash_type).hexdigest()
        headers["Authorization"] = (
            f"BackendAI signMethod=HMAC-{hash_type.upper()}, "
            + f"credential={keypair['access_key']}:{signature}"
        )
        return headers

    return create_header


@pytest.fixture
async def prepare_kernel(
    request, create_app_and_client, get_headers, default_keypair
) -> AsyncIterator[tuple[web.Application, Client, Callable]]:
    sess_id = f"test-kernel-session-{secrets.token_hex(8)}"
    app, client = await create_app_and_client(
        modules=[
            "etcd",
            "events",
            "auth",
            "vfolder",
            "admin",
            "ratelimit",
            "kernel",
            "stream",
            "manager",
        ],
        spawn_agent=True,
    )
    root_ctx: RootContext = app["_root.context"]

    async def create_kernel(image="lua:5.3-alpine", tag=None) -> dict[str, Any]:
        url = "/v3/kernel/"
        req_bytes = json.dumps({
            "image": image,
            "tag": tag,
            "clientSessionToken": sess_id,
        }).encode()
        headers = get_headers("POST", url, req_bytes)
        response = await client.post(url, data=req_bytes, headers=headers)
        return await response.json()

    yield app, client, create_kernel

    try:
        async with root_ctx.db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                sess_id,
            )
            await root_ctx.registry.destroy_session(
                session,
                forced=True,
            )
    except Exception:
        pass


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}

    async def get(self, key: str) -> Any:
        return None


@pytest.fixture
async def registry_ctx(mocker):
    mocked_etcd = DummyEtcd()
    mock_etcd_config_loader = MagicMock()
    mock_etcd_config_loader.update_resource_slots = AsyncMock()
    mock_etcd_config_loader._etcd = mocked_etcd

    mock_loader = MagicMock()
    mock_loader.load = AsyncMock(
        return_value={
            "db": {"name": "test_db", "user": "postgres", "password": "develove"},
            "logging": {},
        }
    )
    mock_config_provider = await ManagerConfigProvider.create(
        loader=mock_loader,
        etcd_watcher=MagicMock(),
        legacy_etcd_config_loader=mock_etcd_config_loader,
    )
    mock_db = MagicMock()
    mock_dbconn = MagicMock()
    mock_dbsess = MagicMock()
    mock_dbconn_ctx = MagicMock()
    mock_dbsess_ctx = MagicMock()
    mock_dbresult = MagicMock()
    mock_dbresult.rowcount = 1
    mock_agent_cache = MagicMock()
    mock_db.connect = MagicMock(return_value=mock_dbconn_ctx)
    mock_db.begin = MagicMock(return_value=mock_dbconn_ctx)
    mock_db.begin_session = MagicMock(return_value=mock_dbsess_ctx)
    mock_dbconn_ctx.__aenter__ = AsyncMock(return_value=mock_dbconn)
    mock_dbconn_ctx.__aexit__ = AsyncMock()
    mock_dbsess_ctx.__aenter__ = AsyncMock(return_value=mock_dbsess)
    mock_dbsess_ctx.__aexit__ = AsyncMock()
    mock_dbconn.execute = AsyncMock(return_value=mock_dbresult)
    mock_dbconn.begin = MagicMock(return_value=mock_dbconn_ctx)
    mock_dbsess.execute = AsyncMock(return_value=mock_dbresult)
    mock_dbsess.begin_session = AsyncMock(return_value=mock_dbsess_ctx)
    mock_valkey_stat_client = MagicMock()
    mock_redis_live = MagicMock()
    mock_redis_live.hset = AsyncMock()
    # Create a mock ValkeyImageClient that satisfies the type requirements
    mock_redis_image = AsyncMock()
    mock_redis_image.close = AsyncMock()  # Add required async methods
    mock_redis_image.get_all_agents_images = AsyncMock(return_value=[])
    mock_redis_image.get_agent_images = AsyncMock(return_value=[])
    mock_redis_image.add_agent_image = AsyncMock()
    mock_redis_image.remove_agent_image = AsyncMock()
    mock_redis_image.remove_agent = AsyncMock()
    mock_redis_image.clear_all_images = AsyncMock()
    mock_event_dispatcher = MagicMock()
    mock_event_producer = MagicMock()
    mock_event_producer.anycast_event = AsyncMock()
    mock_event_producer.broadcast_event = AsyncMock()
    mock_event_producer.anycast_and_broadcast_event = AsyncMock()

    # Create a mock EventHub
    mock_event_hub = MagicMock()
    mock_event_hub.publish = AsyncMock()
    mock_event_hub.subscribe = AsyncMock()
    mock_event_hub.unsubscribe = AsyncMock()

    # mocker.object.patch(mocked_etcd, 'get_prefix', AsyncMock(return_value={}))
    hook_plugin_ctx = HookPluginContext(mocked_etcd, {})  # type: ignore
    network_plugin_ctx = NetworkPluginContext(mocked_etcd, {})  # type: ignore

    # Create a mock scheduling controller
    from ai.backend.common.types import SessionId

    mock_scheduling_controller = AsyncMock()
    mock_scheduling_controller.enqueue_session = AsyncMock(return_value=SessionId(uuid.uuid4()))
    mock_scheduling_controller.dispatch_session_events = AsyncMock()

    registry = AgentRegistry(
        config_provider=mock_config_provider,
        db=mock_db,
        agent_cache=mock_agent_cache,
        valkey_stat=mock_valkey_stat_client,
        valkey_live=mock_redis_live,
        valkey_image=mock_redis_image,
        event_producer=mock_event_producer,
        event_hub=mock_event_hub,
        storage_manager=None,  # type: ignore
        hook_plugin_ctx=hook_plugin_ctx,
        network_plugin_ctx=network_plugin_ctx,
        scheduling_controller=mock_scheduling_controller,  # type: ignore
        manager_public_key=PublicKey(b"GqK]ZYY#h*9jAQbGxSwkeZX3Y*%b+DiY$7ju6sh{"),
        manager_secret_key=SecretKey(b"37KX6]ac^&hcnSaVo=-%eVO9M]ENe8v=BOWF(Sw$"),
        use_sokovan=False,  # Disable sokovan for tests
    )
    await registry.init()
    try:
        yield (
            registry,
            mock_dbconn,
            mock_dbsess,
            mock_dbresult,
            mock_config_provider,
            mock_event_dispatcher,
            mock_event_producer,
        )
    finally:
        await registry.shutdown()


@pytest.fixture(scope="function")
async def session_info(database_engine):
    user_uuid = str(uuid.uuid4()).replace("-", "")
    user_password = str(uuid.uuid4()).replace("-", "")
    password_info = create_test_password_info(user_password)
    postfix = str(uuid.uuid4()).split("-")[1]
    domain_name = str(uuid.uuid4()).split("-")[0]
    group_id = str(uuid.uuid4()).replace("-", "")
    group_name = str(uuid.uuid4()).split("-")[0]
    sgroup_name = str(uuid.uuid4()).split("-")[0]
    session_id = str(uuid.uuid4()).replace("-", "")
    session_creation_id = str(uuid.uuid4()).replace("-", "")

    resource_policy_name = str(uuid.uuid4()).replace("-", "")

    async with database_engine.begin_session() as db_sess:
        scaling_group = ScalingGroupRow(
            name=sgroup_name,
            driver="test",
            scheduler="test",
            scheduler_opts=ScalingGroupOpts(),
        )
        db_sess.add(scaling_group)

        domain = DomainRow(name=domain_name, total_resource_slots={})
        db_sess.add(domain)

        user_resource_policy = UserResourcePolicyRow(
            name=resource_policy_name,
            max_vfolder_count=0,
            max_quota_scope_size=-1,
            max_session_count_per_model_session=10,
            max_customized_image_count=10,
        )
        db_sess.add(user_resource_policy)

        project_resource_policy = ProjectResourcePolicyRow(
            name=resource_policy_name,
            max_vfolder_count=0,
            max_quota_scope_size=-1,
            max_network_count=3,
        )
        db_sess.add(project_resource_policy)

        group = GroupRow(
            id=group_id,
            name=group_name,
            domain_name=domain_name,
            total_resource_slots={},
            resource_policy=resource_policy_name,
        )
        db_sess.add(group)

        user = UserRow(
            uuid=user_uuid,
            email=f"tc.runner-{postfix}@lablup.com",
            username=f"TestCaseRunner-{postfix}",
            password=password_info,
            domain_name=domain_name,
            resource_policy=resource_policy_name,
        )
        db_sess.add(user)

        sess = SessionRow(
            id=session_id,
            creation_id=session_creation_id,
            cluster_size=1,
            domain_name=domain_name,
            scaling_group_name=sgroup_name,
            group_id=group_id,
            user_uuid=user_uuid,
            vfolder_mounts={},
        )
        db_sess.add(sess)

        kern = KernelRow(
            session_id=session_id,
            domain_name=domain_name,
            group_id=group_id,
            user_uuid=user_uuid,
            cluster_role=DEFAULT_ROLE,
            occupied_slots={},
            repl_in_port=0,
            repl_out_port=0,
            stdin_port=0,
            stdout_port=0,
            vfolder_mounts={},
        )
        db_sess.add(kern)

        await db_sess.commit()
        yield session_id, db_sess

        await db_sess.execute(sa.delete(KernelRow).where(KernelRow.session_id == session_id))
        await db_sess.execute(sa.delete(SessionRow).where(SessionRow.id == session_id))
        await db_sess.execute(sa.delete(UserRow).where(UserRow.uuid == user_uuid))
        await db_sess.execute(sa.delete(GroupRow).where(GroupRow.id == group_id))
        await db_sess.execute(
            sa.delete(ProjectResourcePolicyRow).where(
                ProjectResourcePolicyRow.name == resource_policy_name
            )
        )
        await db_sess.execute(
            sa.delete(UserResourcePolicyRow).where(
                UserResourcePolicyRow.name == resource_policy_name
            )
        )
        await db_sess.execute(sa.delete(DomainRow).where(DomainRow.name == domain_name))
        await db_sess.execute(sa.delete(ScalingGroupRow).where(ScalingGroupRow.name == sgroup_name))
