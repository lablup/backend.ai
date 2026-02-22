from __future__ import annotations

import asyncio
import json
import os
import secrets
import shutil
import tempfile
import textwrap
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import AsyncExitStack
from dataclasses import dataclass
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
from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.configs.loader import EtcdConfigWatcher, LoaderChain
from ai.backend.common.configs.pyroscope import PyroscopeConfig
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.jwt.validator import JWTValidator
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot, VFolderHostPermissionMap
from ai.backend.logging import LocalLogger, LogLevel
from ai.backend.logging.config import ConsoleConfig, LogDriver, LoggingConfig
from ai.backend.logging.types import LogFormat
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.cli.context import CLIContext
from ai.backend.manager.cli.dbschema import oneshot as cli_schema_oneshot
from ai.backend.manager.cli.etcd import delete as cli_etcd_delete
from ai.backend.manager.cli.etcd import put_json as cli_etcd_put_json
from ai.backend.manager.config.bootstrap import BootstrapConfig
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import (
    DatabaseConfig,
    DebugConfig,
    ManagerConfig,
    ManagerUnifiedConfig,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
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
from ai.backend.manager.models.vfolder import vfolders
from ai.backend.manager.server import (
    build_root_app,
    etcd_ctx,
    global_subapp_pkgs,
    webapp_plugin_ctx,
)
from ai.backend.testutils.pants import get_parallel_slot

# Import testcontainer fixtures (etcd_container, redis_container, postgres_container)
# via pytest_plugins so they are registered as fixtures without triggering
# F401 (unused-import) or F811 (redefined-while-unused) lint errors.
pytest_plugins = [
    "ai.backend.testutils.bootstrap",
]


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


def pytest_configure(config: pytest.Config) -> None:
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

    # NOTE: model_validate() is used for Pydantic config models below because
    # mypy does not recognize fields with default/default_factory as optional
    # constructor args, causing [call-arg] errors with direct instantiation.
    # model_construct() was also considered but it skips validation and does
    # not populate default values for missing fields, making it unsuitable.
    config = BootstrapConfig(
        etcd=EtcdConfig.model_validate({
            "namespace": test_id,
            "addr": HostPortPairModel(host=etcd_addr.host, port=etcd_addr.port),
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
            "rpc_auth_manager_keypair": build_root / "fixtures" / "manager" / "manager.key_secret",
        }),
        pyroscope=PyroscopeConfig(
            enabled=False,
            app_name="backend.ai-test",
            server_addr="http://localhost:4040",
            sample_rate=100,
        ),
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

    cli_ctx = CLIContext(log_level=LogLevel.DEBUG)
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
def database(
    request: pytest.FixtureRequest, bootstrap_config: BootstrapConfig, test_db: str
) -> None:
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
# Function-scope fixtures
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
    """Insert resource policies (user, project, keypair) with a shared random name."""
    policy_name = f"policy-{secrets.token_hex(6)}"
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
    yield policy_name
    async with db_engine.begin() as conn:
        await conn.execute(
            keypair_resource_policies.delete().where(
                keypair_resource_policies.c.name == policy_name
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
    config_provider: ManagerConfigProvider | None = None
    try:
        await init_stack.enter_async_context(
            etcd_ctx(root_ctx, bootstrap_config.etcd.to_dataclass())
        )

        # Create ManagerConfigProvider directly, bypassing the production
        # config loading pipeline (LoaderChain, TOML parsing, etcd watcher).
        # NOTE: model_validate() is used instead of direct construction because
        # ManagerUnifiedConfig has fields with default_factory (e.g. service_discovery,
        # artifact_registry) that mypy does not recognize as optional constructor args.
        unified_config = ManagerUnifiedConfig.model_validate({
            "db": bootstrap_config.db,
            "etcd": bootstrap_config.etcd,
            "manager": bootstrap_config.manager,
            "logging": bootstrap_config.logging,
            "pyroscope": bootstrap_config.pyroscope,
            "debug": bootstrap_config.debug,
        })
        legacy_etcd_loader = LegacyEtcdLoader(root_ctx.etcd)
        etcd_watcher = EtcdConfigWatcher(root_ctx.etcd)
        loader_chain = LoaderChain([legacy_etcd_loader])
        config_provider = ManagerConfigProvider(
            loader_chain,
            unified_config,
            etcd_watcher,
            legacy_etcd_loader,
        )
        root_ctx.config_provider = config_provider

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
        if config_provider is not None:
            await config_provider.terminate()
        await init_stack.__aexit__(None, None, None)


@pytest.fixture()
async def admin_registry(
    server_factory: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry with superadmin keypair."""
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server_factory.url)),
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
    server_factory: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry with normal-user keypair."""
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server_factory.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()
