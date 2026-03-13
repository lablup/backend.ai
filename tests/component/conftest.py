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
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import asyncpg
import pytest
import sqlalchemy as sa
import yarl
from aiohttp import web
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
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
from ai.backend.common.data.user.types import UserRole
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
from ai.backend.common.message_queue.redis_queue.queue import RedisMQArgs, RedisQueue
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import (
    AgentId,
    DefaultForUnspecified,
    HostPortPair,
    RedisTarget,
    ResourceSlot,
    SlotName,
    SlotTypes,
    VFolderHostPermissionMap,
    current_resource_slots,
)
from ai.backend.logging import LocalLogger, LogLevel
from ai.backend.logging.config import ConsoleConfig, LogDriver, LoggingConfig
from ai.backend.logging.types import LogFormat
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api.rest.app import build_root_app, mount_registries
from ai.backend.manager.api.rest.middleware import build_auth_middleware, build_exception_middleware
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import (
    ALL_ALLOWED,
    READ_ALLOWED,
    server_status_required,
)
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.cli.context import CLIContext
from ai.backend.manager.cli.dbschema import oneshot as cli_schema_oneshot
from ai.backend.manager.cli.etcd import delete as cli_etcd_delete
from ai.backend.manager.cli.etcd import put_json as cli_etcd_put_json
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.bootstrap import BootstrapConfig
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import (
    DatabaseConfig,
    DebugConfig,
    ManagerConfig,
    ManagerUnifiedConfig,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.base import pgsql_connect_opts
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import GroupRow, association_groups_users
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
    keypair_resource_policies,
)
from ai.backend.manager.models.scaling_group import scaling_groups, sgroups_for_domains
from ai.backend.manager.models.scaling_group.row import ScalingGroupOpts
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.session_template import session_templates
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    connect_database,
    create_async_engine,
)
from ai.backend.manager.models.vfolder import vfolders
from ai.backend.manager.notification.notification_center import NotificationCenter
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.auth.service import AuthService
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


@dataclass
class KeypairFixtureData:
    access_key: str
    secret_key: str


@dataclass
class UserFixtureData:
    user_uuid: uuid.UUID
    keypair: KeypairFixtureData
    email: str = ""


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

    # NOTE: All config models below use model_validate() instead of direct
    # constructor calls because the pydantic-mypy plugin does not recognize
    # default values declared via Annotated[..., Field(default=...)], treating
    # every field as required. model_construct() was also considered but
    # rejected because it skips validation entirely and does not populate
    # missing fields with their defaults.
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
                host="127.0.0.1", port=29100 + get_parallel_slot() * 10
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
    try:
        shutil.rmtree(ipc_base_path)
    except OSError:
        pass


@pytest.fixture(scope="session")
def redis_addr(
    redis_container: tuple[str, HostPortPairModel],  # noqa: F811
) -> HostPortPairModel:
    """Expose the Redis container address for fixtures that need it directly."""
    return redis_container[1]


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


@pytest.fixture()
async def db_engine(
    bootstrap_config: BootstrapConfig,
    test_db: str,
    database: None,
) -> AsyncIterator[SAEngine]:
    """Provide a function-scoped SQLAlchemy async engine connected to the test database."""
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
    """Provide a function-scoped ExtendedAsyncSAEngine for repository/service fixtures."""
    async with connect_database(bootstrap_config.db) as db:
        yield db


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
async def resource_policy_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[str]:
    """Insert resource policies (user, project, keypair) with a shared random name.

    Also inserts system-default resource policies ("default") required
    by the user-creation flow:
    - "default" keypair resource policy: always assigned to new keypairs
    - "default" user resource policy: always assigned to new users (e.g. signup)
    Teardown removes both the named policies and the "default" policies.
    The "default" policies are safe to delete here because user_factory
    (which depends on this fixture) runs its teardown first, purging all
    users and keypairs that reference them.
    """
    policy_name = f"policy-{secrets.token_hex(6)}"
    default_policy_name = "default"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(UserResourcePolicyRow.__table__).values(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=3,
            )
        )
        await conn.execute(
            sa.insert(ProjectResourcePolicyRow.__table__).values(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
        )
        await conn.execute(
            sa.insert(keypair_resource_policies).values(
                name=policy_name,
                default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=5,
                max_containers_per_session=1,
                idle_timeout=3600,
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
            )
        )
        # The user-creation flow always assigns new keypairs to the "default"
        # keypair resource policy (DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME).
        # Uses on_conflict_do_nothing() for idempotency in case alembic
        # migrations already seeded the row.
        await conn.execute(
            pg_insert(keypair_resource_policies)
            .values(
                name=default_policy_name,
                default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=5,
                max_containers_per_session=1,
                idle_timeout=3600,
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
            )
            .on_conflict_do_nothing()
        )
        # The signup flow always assigns "default" as the user's resource_policy.
        await conn.execute(
            pg_insert(UserResourcePolicyRow.__table__)
            .values(
                name=default_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=3,
            )
            .on_conflict_do_nothing()
        )
    yield policy_name
    async with db_engine.begin() as conn:
        await conn.execute(
            keypair_resource_policies.delete().where(
                keypair_resource_policies.c.name == default_policy_name
            )
        )
        await conn.execute(
            keypair_resource_policies.delete().where(
                keypair_resource_policies.c.name == policy_name
            )
        )
        await conn.execute(
            UserResourcePolicyRow.__table__.delete().where(
                UserResourcePolicyRow.__table__.c.name == default_policy_name
            )
        )
        await conn.execute(
            UserResourcePolicyRow.__table__.delete().where(
                UserResourcePolicyRow.__table__.c.name == policy_name
            )
        )
        await conn.execute(
            ProjectResourcePolicyRow.__table__.delete().where(
                ProjectResourcePolicyRow.__table__.c.name == policy_name
            )
        )


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


@pytest.fixture()
async def group_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test group (project) and yield its UUID."""
    group_id = uuid.uuid4()
    group_name = f"group-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=group_id,
                name=group_name,
                description=f"Test group {group_name}",
                is_active=True,
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
    yield group_id
    async with db_engine.begin() as conn:
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id))


@pytest.fixture()
async def admin_user_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[UserFixtureData]:
    """Insert admin user, keypair, and group membership; yield identifiers."""
    unique_id = secrets.token_hex(4)
    email = f"admin-{unique_id}@test.local"
    data = UserFixtureData(
        user_uuid=uuid.uuid4(),
        keypair=KeypairFixtureData(
            access_key=f"AKTEST{secrets.token_hex(7).upper()}",
            secret_key=secrets.token_hex(20),
        ),
        email=email,
    )
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(users).values(
                uuid=str(data.user_uuid),
                username=f"admin-{unique_id}",
                email=email,
                password=PasswordInfo(
                    password=secrets.token_urlsafe(8),
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name=f"Admin {unique_id}",
                description=f"Test admin account {unique_id}",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
                role=UserRole.SUPERADMIN,
            )
        )
        await conn.execute(
            sa.insert(keypairs).values(
                user_id=email,
                access_key=data.keypair.access_key,
                secret_key=data.keypair.secret_key,
                is_active=True,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
                num_queries=0,
                is_admin=True,
                user=str(data.user_uuid),
            )
        )
        await conn.execute(
            sa.insert(association_groups_users).values(
                group_id=str(group_fixture),
                user_id=str(data.user_uuid),
            )
        )
    yield data
    async with db_engine.begin() as conn:
        # Clean side-effect tables that tests may populate via the running server
        await conn.execute(vfolders.delete())
        await conn.execute(kernels.delete())
        await conn.execute(SessionRow.__table__.delete())
        await conn.execute(session_templates.delete())
        await conn.execute(ImageAliasRow.__table__.delete())
        await conn.execute(ImageRow.__table__.delete())
        # Clean fixture data
        await conn.execute(
            association_groups_users.delete().where(
                association_groups_users.c.user_id == str(data.user_uuid)
            )
        )
        await conn.execute(
            keypairs.delete().where(keypairs.c.access_key == data.keypair.access_key)
        )
        await conn.execute(users.delete().where(users.c.uuid == str(data.user_uuid)))


@pytest.fixture()
async def regular_user_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[UserFixtureData]:
    """Insert regular user, keypair, and group membership; yield identifiers."""
    unique_id = secrets.token_hex(4)
    email = f"user-{unique_id}@test.local"
    data = UserFixtureData(
        user_uuid=uuid.uuid4(),
        keypair=KeypairFixtureData(
            access_key=f"AKTEST{secrets.token_hex(7).upper()}",
            secret_key=secrets.token_hex(20),
        ),
        email=email,
    )
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(users).values(
                uuid=str(data.user_uuid),
                username=f"user-{unique_id}",
                email=email,
                password=PasswordInfo(
                    password=secrets.token_urlsafe(8),
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name=f"User {unique_id}",
                description=f"Test user account {unique_id}",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
                role=UserRole.USER,
            )
        )
        await conn.execute(
            sa.insert(keypairs).values(
                user_id=email,
                access_key=data.keypair.access_key,
                secret_key=data.keypair.secret_key,
                is_active=True,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
                num_queries=0,
                is_admin=False,
                user=str(data.user_uuid),
            )
        )
        await conn.execute(
            sa.insert(association_groups_users).values(
                group_id=str(group_fixture),
                user_id=str(data.user_uuid),
            )
        )
    yield data
    async with db_engine.begin() as conn:
        # Clean side-effect tables that tests may populate via the running server
        await conn.execute(
            session_templates.delete().where(session_templates.c.user_uuid == str(data.user_uuid))
        )
        # Clean fixture data
        await conn.execute(
            association_groups_users.delete().where(
                association_groups_users.c.user_id == str(data.user_uuid)
            )
        )
        await conn.execute(
            keypairs.delete().where(keypairs.c.access_key == data.keypair.access_key)
        )
        await conn.execute(users.delete().where(users.c.uuid == str(data.user_uuid)))


@pytest.fixture()
async def database_fixture(
    admin_user_fixture: UserFixtureData,
    regular_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[None]:
    """Backward-compatible aggregate: requests all seed data fixtures."""
    yield


class _TestConfigProvider(ManagerConfigProvider):
    """Test-only subclass that provides a ManagerUnifiedConfig directly,
    bypassing the production LoaderChain / TOML parsing / etcd watcher pipeline.

    Only the ``config`` property is functional; production-only attributes
    (_loader, _etcd_watcher, _legacy_etcd_config_loader) are not initialized.
    """

    def __init__(self, config: ManagerUnifiedConfig) -> None:
        # Intentionally skip super().__init__() to avoid requiring
        # LoaderChain, EtcdConfigWatcher, and LegacyEtcdLoader dependencies
        # that are irrelevant in the test environment.
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
        self._legacy_etcd_config_loader = mock_etcd_loader
        # Set the current_resource_slots ContextVar so that ResourceSlot
        # operations (e.g. normalize_slots) work without hitting etcd.
        _slots = {
            SlotName("cpu"): SlotTypes("count"),
            SlotName("mem"): SlotTypes("bytes"),
        }
        current_resource_slots.set(_slots)


@pytest.fixture()
def route_deps(config_provider: ManagerConfigProvider) -> RouteDeps:
    """Shared routing context for test registrar calls."""
    return RouteDeps(
        cors_options={},
        read_status_mw=server_status_required(READ_ALLOWED, config_provider),
        all_status_mw=server_status_required(ALL_ALLOWED, config_provider),
    )


@pytest.fixture()
def server_module_registries() -> list[RouteRegistry]:
    """
    Pre-built route registries to load for the test server.

    Override this fixture in domain-specific conftest.py to build only the
    registries relevant to that domain's tests.
    """
    return []


@pytest.fixture()
def config_provider(
    bootstrap_config: BootstrapConfig,
    redis_addr: HostPortPairModel,
) -> ManagerConfigProvider:
    """Build a test config provider without LoaderChain / etcd watcher."""
    unified_config = ManagerUnifiedConfig.model_validate({
        "db": bootstrap_config.db,
        "etcd": bootstrap_config.etcd,
        "manager": bootstrap_config.manager,
        "logging": bootstrap_config.logging,
        "pyroscope": bootstrap_config.pyroscope,
        "debug": bootstrap_config.debug,
        "redis": {"addr": {"host": redis_addr.host, "port": redis_addr.port}},
    })
    return _TestConfigProvider(unified_config)


# ---------------------------------------------------------------------------
# Real infrastructure fixtures (Valkey, events, plugins, etc.)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def valkey_clients(
    config_provider: ManagerConfigProvider,
) -> AsyncIterator[ValkeyClients]:
    """Real Valkey clients — mirrors ValkeyDependency.provide()."""
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
async def event_producer(
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
) -> AsyncIterator[EventProducer]:
    """Real EventProducer that publishes to Valkey streams."""
    redis_config = config_provider.config.redis
    assert redis_config.addr is not None
    redis_target = RedisTarget(
        addr=HostPortPair(host=redis_config.addr.host, port=redis_config.addr.port),
        redis_helper_config={},
    )
    queue = await RedisQueue.create(
        redis_target,
        RedisMQArgs(
            anycast_stream_key="events",
            broadcast_channel="events_all",
            consume_stream_keys={"events"},
            subscribe_channels={"events_all"},
            group_name=f"test_mq_{uuid4()}",
            node_id=f"test_node_{uuid4()}",
            db=REDIS_STREAM_DB,
        ),
    )
    producer = EventProducer(queue, source=AgentId(f"test-mgr-{uuid4()}"))
    try:
        yield producer
    finally:
        await producer.close()
        await queue.close()


@pytest.fixture()
async def background_task_manager(
    event_producer: EventProducer,
    valkey_clients: ValkeyClients,
) -> AsyncIterator[BackgroundTaskManager]:
    """Real BackgroundTaskManager backed by Valkey."""
    mgr = BackgroundTaskManager(
        event_producer,
        valkey_client=valkey_clients.bgtask,
        server_id=f"test-server-{uuid4()}",
    )
    yield mgr
    await mgr.shutdown()


def _make_async_etcd(bootstrap_config: BootstrapConfig) -> AsyncEtcd:
    """Create an AsyncEtcd instance from bootstrap config."""
    etcd_config = bootstrap_config.etcd
    etcd_addr = etcd_config.addr
    addrs: HostPortPair | list[HostPortPair]
    if isinstance(etcd_addr, list):
        addrs = [HostPortPair(host=a.host, port=a.port) for a in etcd_addr]
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
def async_etcd(
    bootstrap_config: BootstrapConfig,
    etcd_fixture: None,
) -> AsyncEtcd:
    """Real AsyncEtcd client for tests that need direct etcd access."""
    return _make_async_etcd(bootstrap_config)


@pytest.fixture()
def hook_plugin_ctx(
    bootstrap_config: BootstrapConfig,
    etcd_fixture: None,
) -> HookPluginContext:
    """Real HookPluginContext with no plugins loaded."""
    return HookPluginContext(_make_async_etcd(bootstrap_config), {})


@pytest.fixture()
def network_plugin_ctx(
    bootstrap_config: BootstrapConfig,
    etcd_fixture: None,
) -> NetworkPluginContext:
    """Real NetworkPluginContext with no plugins loaded."""
    return NetworkPluginContext(_make_async_etcd(bootstrap_config), {})


@pytest.fixture()
def error_monitor(
    bootstrap_config: BootstrapConfig,
    etcd_fixture: None,
) -> ErrorPluginContext:
    """Real ErrorPluginContext with no plugins loaded."""
    return ErrorPluginContext(_make_async_etcd(bootstrap_config), {})


@pytest.fixture()
def stats_monitor(
    bootstrap_config: BootstrapConfig,
    etcd_fixture: None,
) -> StatsPluginContext:
    """Real StatsPluginContext with no plugins loaded."""
    return StatsPluginContext(_make_async_etcd(bootstrap_config), {})


@pytest.fixture()
async def notification_center() -> AsyncIterator[NotificationCenter]:
    """Real NotificationCenter."""
    nc = NotificationCenter()
    yield nc
    await nc.close()


# ---------------------------------------------------------------------------
# External component mocks (talk to separate Backend.AI processes)
# ---------------------------------------------------------------------------


@pytest.fixture()
def storage_manager() -> StorageSessionManager:
    """Mock — talks to Storage Proxy (external component)."""
    return AsyncMock(spec=StorageSessionManager)


@pytest.fixture()
def agent_registry() -> AgentRegistry:
    """Mock — talks to Agent nodes (external component)."""
    return AsyncMock(spec=AgentRegistry)


@pytest.fixture()
def agent_cache() -> AgentRPCCache:
    """Mock — talks to Agent RPC (external component)."""
    return AsyncMock(spec=AgentRPCCache)


@pytest.fixture()
def appproxy_client_pool() -> AppProxyClientPool:
    """Mock — talks to AppProxy (external component)."""
    return AsyncMock(spec=AppProxyClientPool)


# ---------------------------------------------------------------------------
# Shared auth_processors fixture (used by many domain conftests)
# ---------------------------------------------------------------------------


@pytest.fixture()
def auth_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    hook_plugin_ctx: HookPluginContext,
) -> AuthProcessors:
    """Real AuthProcessors wired with real AuthService and AuthRepository."""
    repo = AuthRepository(database_engine)
    service = AuthService(
        hook_plugin_ctx=hook_plugin_ctx,
        auth_repository=repo,
        config_provider=config_provider,
    )
    return AuthProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


# ---------------------------------------------------------------------------
# Server fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
async def server(
    bootstrap_config: BootstrapConfig,
    etcd_fixture: None,
    database_fixture: None,
    server_module_registries: list[RouteRegistry],
    config_provider: ManagerConfigProvider,
    error_monitor: ErrorPluginContext,
    stats_monitor: StatsPluginContext,
    valkey_clients: ValkeyClients,
    hook_plugin_ctx: HookPluginContext,
) -> AsyncIterator[ServerInfo]:
    """Start a test server with real DB, real plugin contexts, and real Valkey."""
    app = build_root_app(
        0,
        bootstrap_config,
    )

    cp = config_provider

    # Real DB connection for HMAC auth middleware
    async with connect_database(cp.config.db) as db:
        # JWT validator mock — HMAC auth only, JWT not called in tests
        jwt_validator = MagicMock()

        # Insert DI-based middlewares with real plugin contexts
        app.middlewares.insert(
            1,
            build_exception_middleware(
                error_monitor=error_monitor,
                stats_monitor=stats_monitor,
                config_provider=cp,
            ),
        )
        app.middlewares.insert(
            2,
            build_auth_middleware(
                db=db,
                jwt_validator=jwt_validator,
                valkey_stat=valkey_clients.stat,
                hook_plugin_ctx=hook_plugin_ctx,
            ),
        )

        if server_module_registries:
            mount_registries(app, server_module_registries)

        runner = web.AppRunner(app, handle_signals=False)
        await runner.setup()
        service_addr = cp.config.manager.service_addr
        site = web.TCPSite(
            runner,
            service_addr.host,
            service_addr.port,
            reuse_port=True,
        )
        await site.start()

        yield ServerInfo(host=str(service_addr.host), port=service_addr.port)

        await runner.cleanup()


@pytest.fixture()
async def admin_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry with superadmin keypair."""
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def user_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry with normal-user keypair."""
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()
