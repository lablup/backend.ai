"""Fixtures for AgentService unit/integration tests.

These tests exercise AgentService with a real database and Valkey, so they
provide infrastructure fixtures that override the guard defined in
tests/unit/manager/services/conftest.py.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import tempfile
import textwrap
from collections.abc import AsyncIterator, Callable, Coroutine, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import asyncpg
import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.configs.pyroscope import PyroscopeConfig
from ai.backend.common.defs import (
    REDIS_BGTASK_DB,
    REDIS_CONTAINER_LOG,
    REDIS_IMAGE_DB,
    REDIS_LIVE_DB,
    REDIS_RATE_LIMIT_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
    RedisRole,
)
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import (
    AgentId,
    HostPortPair,
    ResourceSlot,
    SlotName,
    SlotTypes,
    VFolderHostPermissionMap,
    current_resource_slots,
)
from ai.backend.logging import LogLevel
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.cli.context import CLIContext
from ai.backend.manager.cli.dbschema import oneshot as cli_schema_oneshot
from ai.backend.manager.cli.etcd import delete as cli_etcd_delete
from ai.backend.manager.cli.etcd import put_json as cli_etcd_put_json
from ai.backend.manager.config.bootstrap import BootstrapConfig
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import (
    DatabaseConfig,
    DebugConfig,
    ManagerConfig,
    ManagerUnifiedConfig,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.base import pgsql_connect_opts
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.resource_slot import ResourceSlotTypeRow
from ai.backend.manager.models.scaling_group import scaling_groups, sgroups_for_domains
from ai.backend.manager.models.scaling_group.row import ScalingGroupOpts
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    connect_database,
    create_async_engine,
)
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.testutils.bootstrap import (  # noqa: F401
    etcd_container,
    postgres_container,
    redis_container,
)
from ai.backend.testutils.pants import get_parallel_slot

# ---------------------------------------------------------------------------
# Infrastructure fixtures (override the guard in services/conftest.py)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def bootstrap_config(
    test_id: str,
    ipc_base_path: Path,
    logging_config: Any,
    etcd_container: tuple[str, HostPortPairModel],  # noqa: F811
    redis_container: tuple[str, HostPortPairModel],  # noqa: F811
    postgres_container: tuple[str, HostPortPairModel],  # noqa: F811
    test_db: str,
) -> Iterator[BootstrapConfig]:
    etcd_addr = etcd_container[1]
    postgres_addr = postgres_container[1]

    build_root = Path(os.environ["BACKEND_BUILD_ROOT"])

    config = BootstrapConfig(
        etcd=EtcdConfig.model_validate({
            "namespace": test_id,
            "addr": {"host": etcd_addr.host, "port": etcd_addr.port},
        }),
        db=DatabaseConfig.model_validate({
            "addr": postgres_addr,
            "name": test_db,
            "user": "postgres",
            "password": "develove",
            "pool_size": 8,
            "pool_recycle": -1,
            "pool_pre_ping": False,
            "max_overflow": 64,
            "lock_conn_timeout": 0,
        }),
        manager=ManagerConfig.model_validate({
            "id": f"i-{test_id}",
            "num_proc": 1,
            "distributed_lock": "filelock",
            "ipc_base_path": ipc_base_path,
            "service_addr": HostPortPairModel(
                host="127.0.0.1", port=29200 + get_parallel_slot() * 10
            ),
            "allowed_plugins": set(),
            "disabled_plugins": set(),
            "rpc_auth_manager_keypair": f"{build_root}/fixtures/manager/manager.key_secret",
        }),
        pyroscope=PyroscopeConfig.model_validate({
            "enabled": False,
            "app_name": "backend.ai-test",
            "server_addr": "http://localhost:4040",
            "sample_rate": 100,
        }),
        debug=DebugConfig.model_validate({
            "enabled": False,
            "log_events": False,
            "log_scheduler_ticks": False,
            "periodic_sync_stats": False,
        }),
        logging=logging_config,
    )

    yield config


@pytest.fixture(scope="session")
def redis_addr(
    redis_container: tuple[str, HostPortPairModel],  # noqa: F811
) -> HostPortPairModel:
    return redis_container[1]


@pytest.fixture(scope="session")
def etcd_fixture(
    test_id: str,
    bootstrap_config: BootstrapConfig,
    redis_container: tuple[str, HostPortPairModel],  # noqa: F811
) -> Iterator[None]:
    """Load minimal etcd config required for AgentService tests."""
    _redis_addr = redis_container[1]

    cli_ctx = CLIContext(log_level=LogLevel.DEBUG)
    cli_ctx._bootstrap_config = bootstrap_config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".etcd.json") as f:
        etcd_data = {
            "manager": {"status": "running"},
            "config": {
                "redis": {
                    "addr": f"{_redis_addr.host}:{_redis_addr.port}",
                },
            },
            "nodes": {},
        }
        json.dump(etcd_data, f)
        f.flush()
        click_ctx = cli_etcd_put_json.make_context("test", ["", f.name], obj=cli_ctx)
        click_ctx.obj = cli_ctx
        cli_etcd_put_json.invoke(click_ctx)
    yield
    click_ctx = cli_etcd_delete.make_context("test", ["--prefix", ""], obj=cli_ctx)
    cli_etcd_delete.invoke(click_ctx)


@pytest.fixture(scope="session")
def database(
    request: pytest.FixtureRequest,
    bootstrap_config: BootstrapConfig,
    test_db: str,
) -> None:
    """Create a test database and install the full schema via alembic."""
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


@pytest.fixture()
async def db_engine(
    bootstrap_config: BootstrapConfig,
    test_db: str,
    database: None,
) -> AsyncIterator[SAEngine]:
    """Function-scoped SQLAlchemy engine connected to the test database."""
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
    yield engine
    await engine.dispose()


@pytest.fixture()
async def database_engine(
    bootstrap_config: BootstrapConfig,
    database: None,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    """ExtendedAsyncSAEngine — overrides the guard in services/conftest.py."""
    async with connect_database(bootstrap_config.db) as db:
        yield db


@pytest.fixture()
def config_provider(
    bootstrap_config: BootstrapConfig,
    redis_addr: HostPortPairModel,
) -> ManagerConfigProvider:
    """Minimal ManagerConfigProvider for AgentService construction."""
    unified_config = ManagerUnifiedConfig.model_validate({
        "db": bootstrap_config.db,
        "etcd": bootstrap_config.etcd,
        "manager": bootstrap_config.manager,
        "logging": bootstrap_config.logging,
        "pyroscope": bootstrap_config.pyroscope,
        "debug": bootstrap_config.debug,
        "redis": {"addr": {"host": redis_addr.host, "port": redis_addr.port}},
    })

    class _TestConfigProvider(ManagerConfigProvider):
        def __init__(self, config: ManagerUnifiedConfig) -> None:
            self._config = config
            self._etcd_watcher_task = None
            mock_etcd_loader = MagicMock()
            mock_etcd_loader.get_manager_status = AsyncMock(return_value=ManagerStatus.RUNNING)
            mock_etcd_loader.get_allowed_origins = AsyncMock(return_value=None)
            mock_etcd_loader.get_vfolder_types = AsyncMock(return_value=["user"])
            mock_etcd_loader.get_resource_slots = AsyncMock(
                return_value={
                    SlotName("cpu"): SlotTypes("count"),
                    SlotName("mem"): SlotTypes("bytes"),
                }
            )
            mock_etcd_loader.get_raw = AsyncMock(return_value="true")
            mock_etcd_loader.update_manager_status = AsyncMock()
            mock_etcd_loader.get_manager_nodes_info = AsyncMock(return_value={})
            mock_etcd_loader.register_myself = AsyncMock()
            mock_etcd_loader.deregister_myself = AsyncMock()
            mock_etcd_loader.update_resource_slots = AsyncMock()
            self._legacy_etcd_config_loader = mock_etcd_loader
            _slots = {
                SlotName("cpu"): SlotTypes("count"),
                SlotName("mem"): SlotTypes("bytes"),
            }
            current_resource_slots.set(_slots)

    return _TestConfigProvider(unified_config)


@pytest.fixture()
async def valkey_clients(
    config_provider: ManagerConfigProvider,
) -> AsyncIterator[ValkeyClients]:
    """Real Valkey clients for AgentRepository construction."""
    valkey_profile_target = config_provider.config.redis.to_valkey_profile_target()
    clients = ValkeyClients(
        artifact=await ValkeyArtifactDownloadTrackingClient.create(
            valkey_profile_target.profile_target(RedisRole.STATISTICS),
            db_id=REDIS_STATISTICS_DB,
            human_readable_name="test_artifact",
        ),
        container_log=await ValkeyContainerLogClient.create(
            valkey_profile_target.profile_target(RedisRole.CONTAINER_LOG),
            db_id=REDIS_CONTAINER_LOG,
            human_readable_name="test_container_log",
        ),
        live=await ValkeyLiveClient.create(
            valkey_profile_target.profile_target(RedisRole.LIVE),
            db_id=REDIS_LIVE_DB,
            human_readable_name="test_live",
        ),
        stat=await ValkeyStatClient.create(
            valkey_profile_target.profile_target(RedisRole.STATISTICS),
            db_id=REDIS_STATISTICS_DB,
            human_readable_name="test_stat",
        ),
        image=await ValkeyImageClient.create(
            valkey_profile_target.profile_target(RedisRole.IMAGE),
            db_id=REDIS_IMAGE_DB,
            human_readable_name="test_image",
        ),
        stream=await ValkeyStreamClient.create(
            valkey_profile_target.profile_target(RedisRole.STREAM),
            db_id=REDIS_STREAM_DB,
            human_readable_name="test_stream",
        ),
        schedule=await ValkeyScheduleClient.create(
            valkey_profile_target.profile_target(RedisRole.STREAM),
            db_id=REDIS_LIVE_DB,
            human_readable_name="test_schedule",
        ),
        bgtask=await ValkeyBgtaskClient.create(
            valkey_profile_target.profile_target(RedisRole.BGTASK),
            db_id=REDIS_BGTASK_DB,
            human_readable_name="test_bgtask",
        ),
        rate_limit=await ValkeyRateLimitClient.create(
            valkey_profile_target.profile_target(RedisRole.RATE_LIMIT),
            db_id=REDIS_RATE_LIMIT_DB,
            human_readable_name="test_ratelimit",
        ),
    )
    try:
        yield clients
    finally:
        await clients.close()


@pytest.fixture()
def async_etcd(
    bootstrap_config: BootstrapConfig,
    etcd_fixture: None,
) -> AsyncEtcd:
    """Real AsyncEtcd client."""
    etcd_config = bootstrap_config.etcd
    etcd_addr = etcd_config.addr
    if isinstance(etcd_addr, list):
        addrs: HostPortPair | list[HostPortPair] = [
            HostPortPair(host=a.host, port=a.port) for a in etcd_addr
        ]
    else:
        addrs = HostPortPair(host=etcd_addr.host, port=etcd_addr.port)
    return AsyncEtcd(
        addrs=addrs,
        namespace=etcd_config.namespace,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "global",
            ConfigScopes.SGROUP: "sgroup/default",
            ConfigScopes.NODE: "node/test",
        },
    )


@pytest.fixture()
async def domain_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[str]:
    """Insert a test domain and yield its name."""
    domain_name = f"domain-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(domains).values(
                name=domain_name,
                description=f"Test domain {domain_name}",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
            )
        )
    yield domain_name
    async with db_engine.begin() as conn:
        await conn.execute(domains.delete().where(domains.c.name == domain_name))


@pytest.fixture()
async def scaling_group_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
) -> AsyncIterator[str]:
    """Insert a scaling group and its domain association; yield the name."""
    sgroup_name = f"sgroup-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(scaling_groups).values(
                name=sgroup_name,
                description=f"Test scaling group {sgroup_name}",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
        )
        await conn.execute(
            sa.insert(sgroups_for_domains).values(
                scaling_group=sgroup_name,
                domain=domain_fixture,
            )
        )
    yield sgroup_name
    async with db_engine.begin() as conn:
        await conn.execute(
            sgroups_for_domains.delete().where(sgroups_for_domains.c.scaling_group == sgroup_name)
        )
        await conn.execute(scaling_groups.delete().where(scaling_groups.c.name == sgroup_name))


# ---------------------------------------------------------------------------
# AgentService lifecycle fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def lifecycle_agent_service(
    database_engine: ExtendedAsyncSAEngine,
    valkey_clients: ValkeyClients,
    async_etcd: AsyncEtcd,
) -> AsyncIterator[tuple[AgentService, AsyncMock, AsyncMock, MagicMock]]:
    """AgentService wired to real DB + Valkey with mocked external dependencies.

    Yields (service, mock_event_producer, mock_hook_ctx, mock_agent_cache).
    """
    mock_config = MagicMock(spec=ManagerConfigProvider)
    mock_config.config.watcher.token = "test-watcher-token"
    mock_config.legacy_etcd_config_loader.update_resource_slots = AsyncMock()

    agent_repo = AgentRepository(
        database_engine,
        valkey_clients.image,
        valkey_clients.live,
        valkey_clients.stat,
        mock_config,
    )
    scheduler_repo = SchedulerRepository(database_engine, valkey_clients.stat, mock_config)

    mock_event_producer = AsyncMock(spec=EventProducer)
    mock_hook_ctx = AsyncMock(spec=HookPluginContext)
    mock_agent_cache: MagicMock = MagicMock(spec=AgentRPCCache)

    service = AgentService(
        etcd=async_etcd,
        agent_registry=AsyncMock(),
        config_provider=mock_config,
        agent_repository=agent_repo,
        scheduler_repository=scheduler_repo,
        hook_plugin_ctx=mock_hook_ctx,
        event_producer=mock_event_producer,
        agent_cache=mock_agent_cache,
    )
    yield service, mock_event_producer, mock_hook_ctx, mock_agent_cache


@pytest.fixture()
async def agent_row_factory(
    db_engine: SAEngine,
    scaling_group_fixture: str,
) -> AsyncIterator[Callable[..., Coroutine[Any, Any, AgentId]]]:
    """Factory that inserts AgentRow into DB and cleans up on teardown."""
    created_ids: list[str] = []

    async def _create(
        agent_id: str | None = None,
        status: AgentStatus = AgentStatus.ALIVE,
    ) -> AgentId:
        aid = agent_id or f"i-test-{secrets.token_hex(4)}"
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(AgentRow.__table__).values(
                    id=aid,
                    status=status,
                    region="test-region",
                    scaling_group=scaling_group_fixture,
                    available_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                    occupied_slots=ResourceSlot(),
                    addr="http://127.0.0.1:6001",
                    public_host="127.0.0.1",
                    version="24.09.0",
                    architecture="x86_64",
                    compute_plugins={},
                    auto_terminate_abusing_kernel=False,
                )
            )
        created_ids.append(aid)
        return AgentId(aid)

    yield _create

    async with db_engine.begin() as conn:
        for aid in reversed(created_ids):
            await conn.execute(AgentRow.__table__.delete().where(AgentRow.__table__.c.id == aid))


_HEARTBEAT_SLOT_TYPES = [
    {"slot_name": "cpu", "slot_type": "count", "rank": 40},
    {"slot_name": "mem", "slot_type": "bytes", "rank": 50},
]


@pytest.fixture()
async def resource_slot_types_seeded(
    db_engine: SAEngine,
) -> AsyncIterator[None]:
    """Seed resource_slot_types with cpu/mem for handle_heartbeat tests."""
    async with db_engine.begin() as conn:
        for row in _HEARTBEAT_SLOT_TYPES:
            result = await conn.execute(
                sa.select(sa.func.count()).where(
                    ResourceSlotTypeRow.__table__.c.slot_name == row["slot_name"]
                )
            )
            if result.scalar_one() == 0:
                await conn.execute(sa.insert(ResourceSlotTypeRow.__table__).values(**row))

    yield
