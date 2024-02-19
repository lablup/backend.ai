import asyncio
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
from functools import partial
from pathlib import Path
from typing import (
    Any,
    AsyncContextManager,
    AsyncIterator,
    Iterator,
    List,
    Mapping,
    Sequence,
    Tuple,
    Type,
)
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import quote_plus as urlquote

import aiohttp
import asyncpg
import pytest
import sqlalchemy as sa
from aiohttp import web
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common import config
from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.config import ConfigurationError, etcd_config_iv, redis_config_iv
from ai.backend.common.logging import LocalLogger
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import HostPortPair
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.cli.context import CLIContext
from ai.backend.manager.cli.dbschema import oneshot as cli_schema_oneshot
from ai.backend.manager.cli.etcd import delete as cli_etcd_delete
from ai.backend.manager.cli.etcd import put_json as cli_etcd_put_json
from ai.backend.manager.config import LocalConfig, SharedConfig
from ai.backend.manager.config import load as load_config
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models import (
    DomainRow,
    GroupRow,
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
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.models.utils import connect_database
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.server import build_root_app
from ai.backend.testutils.bootstrap import (  # noqa: F401
    etcd_container,
    postgres_container,
    redis_container,
)
from ai.backend.testutils.pants import get_parallel_slot

here = Path(__file__).parent

log = logging.getLogger("tests.manager.conftest")


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
    config = {
        "drivers": ["console"],
        "console": {"colored": None, "format": "verbose"},
        "level": "DEBUG",
        "pkg-ns": {
            "": "INFO",
            "ai.backend": "DEBUG",
            "tests": "DEBUG",
            "alembic": "INFO",
            "aiotools": "INFO",
            "aiohttp": "INFO",
            "sqlalchemy": "WARNING",
        },
    }
    logger = LocalLogger(config)
    with logger:
        yield config


@pytest.fixture(scope="session")
def local_config(
    test_id,
    logging_config,
    etcd_container,  # noqa: F811
    redis_container,  # noqa: F811
    postgres_container,  # noqa: F811
    test_db,
) -> Iterator[LocalConfig]:
    ipc_base_path = Path.cwd() / f"tmp/backend.ai/manager-testing/ipc-{test_id}"
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    etcd_addr = etcd_container[1]
    redis_addr = redis_container[1]
    postgres_addr = postgres_container[1]

    # Establish a self-contained config.
    cfg = LocalConfig({
        **etcd_config_iv.check({
            "etcd": {
                "namespace": test_id,
                "addr": {"host": etcd_addr.host, "port": etcd_addr.port},
            },
        }),
        "redis": redis_config_iv.check({
            "addr": {
                "host": redis_addr.host,
                "port": redis_addr.port,
            },
            "redis_helper_config": config.redis_helper_default_config,
        }),
        "db": {
            "addr": postgres_addr,
            "name": test_db,
            "user": "postgres",
            "password": "develove",
            "pool-size": 8,
            "pool-recycle": -1,
            "max-overflow": 64,
            "lock-conn-timeout": 0,
        },
        "manager": {
            "id": f"i-{test_id}",
            "num-proc": 1,
            "distributed-lock": "filelock",
            "ipc-base-path": ipc_base_path,
            "service-addr": HostPortPair("127.0.0.1", 29100 + get_parallel_slot() * 10),
            "allowed-plugins": set(),
            "disabled-plugins": set(),
        },
        "debug": {
            "enabled": False,
            "log-events": False,
            "log-scheduler-ticks": False,
            "periodic-sync-stats": False,
        },
        "logging": logging_config,
    })

    def _override_if_exists(src: dict, dst: dict, key: str) -> None:
        sentinel = object()
        if (val := src.get(key, sentinel)) is not sentinel:
            dst[key] = val

    try:
        # Override external database config with the current environment's config.
        fs_local_config = load_config()
        cfg["etcd"]["addr"] = fs_local_config["etcd"]["addr"]
        _override_if_exists(fs_local_config["etcd"], cfg["etcd"], "user")
        _override_if_exists(fs_local_config["etcd"], cfg["etcd"], "password")
        cfg["redis"]["addr"] = fs_local_config["redis"]["addr"]
        _override_if_exists(fs_local_config["redis"], cfg["redis"], "password")
        cfg["db"]["addr"] = fs_local_config["db"]["addr"]
        _override_if_exists(fs_local_config["db"], cfg["db"], "user")
        _override_if_exists(fs_local_config["db"], cfg["db"], "password")
    except ConfigurationError:
        pass
    yield cfg
    try:
        shutil.rmtree(ipc_base_path)
    except IOError:
        pass


@pytest.fixture(scope="session")
def etcd_fixture(
    test_id, local_config, vfolder_mount, vfolder_fsprefix, vfolder_host
) -> Iterator[None]:
    # Clear and reset etcd namespace using CLI functions.
    redis_addr = local_config["redis"]["addr"]
    cli_ctx = CLIContext(
        config_path=Path.cwd() / "dummy-manager.toml",
        log_level="DEBUG",
    )
    cli_ctx._local_config = local_config  # override the lazy-loaded config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".etcd.json") as f:
        etcd_fixture = {
            "volumes": {
                "_mount": str(vfolder_mount),
                "_fsprefix": str(vfolder_fsprefix),
                "_default_host": str(vfolder_host),
            },
            "nodes": {},
            "config": {
                "docker": {
                    "registry": {
                        "cr.backend.ai": {
                            "": "https://cr.backend.ai",
                            "type": "harbor2",
                            "project": "stable",
                        },
                    },
                },
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
async def shared_config(app, etcd_fixture):
    root_ctx: RootContext = app["_root.context"]
    shared_config = SharedConfig(
        root_ctx.local_config["etcd"]["addr"],
        root_ctx.local_config["etcd"]["user"],
        root_ctx.local_config["etcd"]["password"],
        root_ctx.local_config["etcd"]["namespace"],
    )
    await shared_config.reload()
    root_ctx: RootContext = app["_root.context"]
    root_ctx.shared_config = shared_config
    yield shared_config


@pytest.fixture(scope="session")
def database(request, local_config, test_db):
    """
    Create a new database for the current test session
    and install the table schema using alembic.
    """
    db_addr = local_config["db"]["addr"]
    db_user = local_config["db"]["user"]
    db_pass = local_config["db"]["password"]

    # Create database using low-level core API.
    # Temporarily use "testing" dbname until we create our own db.
    if db_pass:
        db_url = f"postgresql+asyncpg://{urlquote(db_user)}:{urlquote(db_pass)}@{db_addr}/testing"
    else:
        db_url = f"postgresql+asyncpg://{urlquote(db_user)}@{db_addr}/testing"

    async def init_db():
        engine = sa.ext.asyncio.create_async_engine(
            db_url,
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

    async def finalize_db():
        engine = sa.ext.asyncio.create_async_engine(
            db_url,
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
        log_level="DEBUG",
    )
    cli_ctx._local_config = local_config  # override the lazy-loaded config
    sqlalchemy_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_addr}/{test_db}"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf8") as alembic_cfg:
        alembic_cfg_data = alembic_config_template.format(
            sqlalchemy_url=sqlalchemy_url,
        )
        alembic_cfg.write(alembic_cfg_data)
        alembic_cfg.flush()
        click_ctx = cli_schema_oneshot.make_context(
            "test",
            ["-f", alembic_cfg.name],
            obj=cli_ctx,
        )
        cli_schema_oneshot.invoke(click_ctx)


@pytest.fixture()
async def database_engine(local_config, database):
    async with connect_database(local_config) as db:
        yield db


@pytest.fixture()
def database_fixture(local_config, test_db, database):
    """
    Populate the example data as fixtures to the database
    and delete them after use.
    """
    db_addr = local_config["db"]["addr"]
    db_user = local_config["db"]["user"]
    db_pass = local_config["db"]["password"]
    db_url = f"postgresql+asyncpg://{db_user}:{urlquote(db_pass)}@{db_addr}/{test_db}"

    build_root = Path(os.environ["BACKEND_BUILD_ROOT"])
    fixture_paths = [
        build_root / "fixtures" / "manager" / "example-users.json",
        build_root / "fixtures" / "manager" / "example-keypairs.json",
        build_root / "fixtures" / "manager" / "example-set-user-main-access-keys.json",
        build_root / "fixtures" / "manager" / "example-resource-presets.json",
    ]

    async def init_fixture():
        engine: SAEngine = sa.ext.asyncio.create_async_engine(
            db_url,
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

    asyncio.run(init_fixture())

    yield

    async def clean_fixture():
        engine: SAEngine = sa.ext.asyncio.create_async_engine(
            db_url,
            connect_args=pgsql_connect_opts,
        )
        try:
            async with engine.begin() as conn:
                await conn.execute((vfolders.delete()))
                await conn.execute((kernels.delete()))
                await conn.execute((agents.delete()))
                await conn.execute((keypairs.delete()))
                await conn.execute((users.delete()))
                await conn.execute((scaling_groups.delete()))
                await conn.execute((domains.delete()))
        finally:
            await engine.dispose()

    asyncio.run(clean_fixture())


@pytest.fixture
def file_lock_factory(local_config, request):
    from ai.backend.common.lock import FileLock

    def _make_lock(lock_id):
        lock_path = local_config["manager"]["ipc-base-path"] / f"testing.{lock_id}.lock"
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
async def app(local_config, event_loop):
    """
    Create an empty application with the test configuration.
    """
    return build_root_app(
        0,
        local_config,
        cleanup_contexts=[],
        subapp_pkgs=[],
    )


@pytest.fixture
async def create_app_and_client(local_config, event_loop) -> AsyncIterator:
    client: Client | None = None
    client_session: aiohttp.ClientSession | None = None
    runner: web.BaseRunner | None = None
    _outer_ctxs: List[AsyncContextManager] = []

    async def app_builder(
        cleanup_contexts: Sequence[CleanupContext] = None,
        subapp_pkgs: Sequence[str] = None,
        scheduler_opts: Mapping[str, Any] = None,
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
                if ctx.__name__ in ["shared_config_ctx", "webapp_plugins_ctx"]:
                    _outer_ctx_classes.append(ctx)  # type: ignore
                else:
                    _cleanup_ctxs.append(ctx)
        app = build_root_app(
            0,
            local_config,
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
            str(root_ctx.local_config["manager"]["service-addr"].host),
            root_ctx.local_config["manager"]["service-addr"].port,
            reuse_port=True,
        )
        await site.start()
        port = root_ctx.local_config["manager"]["service-addr"].port
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
def get_headers(app, default_keypair):
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
        root_ctx: RootContext = app["_root.context"]
        hostname = f"127.0.0.1:{root_ctx.local_config['manager']['service-addr'].port}"
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
            + f'credential={keypair["access_key"]}:{signature}'
        )
        return headers

    return create_header


@pytest.fixture
async def prepare_kernel(request, create_app_and_client, get_headers, default_keypair):
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

    async def create_kernel(image="lua:5.3-alpine", tag=None):
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

    access_key = default_keypair["access_key"]
    try:
        await root_ctx.registry.destroy_session(sess_id, access_key)
    except Exception:
        pass


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}

    async def get(self, key: str) -> Any:
        return None


@pytest.fixture
async def registry_ctx(mocker):
    mock_local_config = MagicMock()
    mock_shared_config = MagicMock()
    mock_shared_config.update_resource_slots = AsyncMock()
    mocked_etcd = DummyEtcd()
    mock_shared_config.etcd = mocked_etcd
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
    mock_redis_stat = MagicMock()
    mock_redis_live = MagicMock()
    mock_redis_live.hset = AsyncMock()
    mock_redis_image = MagicMock()
    mock_redis_stream = MagicMock()
    mock_event_dispatcher = MagicMock()
    mock_event_producer = MagicMock()
    mock_event_producer.produce_event = AsyncMock()
    # mocker.object.patch(mocked_etcd, 'get_prefix', AsyncMock(return_value={}))
    hook_plugin_ctx = HookPluginContext(mocked_etcd, {})  # type: ignore

    registry = AgentRegistry(
        local_config=mock_local_config,
        shared_config=mock_shared_config,
        db=mock_db,
        redis_stat=mock_redis_stat,
        redis_live=mock_redis_live,
        redis_image=mock_redis_image,
        redis_stream=mock_redis_stream,
        event_dispatcher=mock_event_dispatcher,
        event_producer=mock_event_producer,
        storage_manager=None,  # type: ignore
        hook_plugin_ctx=hook_plugin_ctx,
        agent_cache=mock_agent_cache,
        manager_public_key=PublicKey(b"GqK]ZYY#h*9jAQbGxSwkeZX3Y*%b+DiY$7ju6sh{"),
        manager_secret_key=SecretKey(b"37KX6]ac^&hcnSaVo=-%eVO9M]ENe8v=BOWF(Sw$"),
    )
    await registry.init()
    try:
        yield (
            registry,
            mock_dbconn,
            mock_dbsess,
            mock_dbresult,
            mock_shared_config,
            mock_event_dispatcher,
            mock_event_producer,
        )
    finally:
        await registry.shutdown()


@pytest.fixture(scope="function")
async def session_info(database_engine):
    user_uuid = str(uuid.uuid4()).replace("-", "")
    user_password = str(uuid.uuid4()).replace("-", "")
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
            name=resource_policy_name, max_vfolder_count=0, max_quota_scope_size=-1
        )
        db_sess.add(user_resource_policy)

        project_resource_policy = ProjectResourcePolicyRow(
            name=resource_policy_name, max_vfolder_count=0, max_quota_scope_size=-1
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
            password=user_password,
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
