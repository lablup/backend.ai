from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.types import HostPortPair, ResourceSlot
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.error_log.handler import ErrorLogHandler
from ai.backend.manager.api.rest.error_log.registry import register_error_log_routes
from ai.backend.manager.api.rest.manager.handler import ManagerHandler
from ai.backend.manager.api.rest.manager.registry import register_manager_api_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.bootstrap import BootstrapConfig
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.agent import agents
from ai.backend.manager.models.error_logs import error_logs
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.error_log.repository import ErrorLogRepository
from ai.backend.manager.repositories.manager_admin.repository import ManagerAdminRepository
from ai.backend.manager.services.error_log.processors import ErrorLogProcessors
from ai.backend.manager.services.error_log.service import ErrorLogService
from ai.backend.manager.services.manager_admin.processors import ManagerAdminProcessors
from ai.backend.manager.services.manager_admin.service import ManagerAdminService


@pytest.fixture()
def error_log_processors(database_engine: ExtendedAsyncSAEngine) -> ErrorLogProcessors:
    repo = ErrorLogRepository(database_engine)
    service = ErrorLogService(repo)
    return ErrorLogProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def manager_admin_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    bootstrap_config: BootstrapConfig,
    valkey_clients: ValkeyClients,
) -> ManagerAdminProcessors:
    etcd_config = bootstrap_config.etcd
    etcd_addr = etcd_config.addr
    if isinstance(etcd_addr, list):
        addrs: HostPortPair | list[HostPortPair] = [
            HostPortPair(host=a.host, port=a.port) for a in etcd_addr
        ]
    else:
        addrs = HostPortPair(host=etcd_addr.host, port=etcd_addr.port)
    etcd = AsyncEtcd(
        addrs=addrs,
        namespace=etcd_config.namespace,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "global",
            ConfigScopes.SGROUP: "sgroup/default",
            ConfigScopes.NODE: "node/test",
        },
    )
    repo = ManagerAdminRepository(database_engine)
    service = ManagerAdminService(
        repository=repo,
        config_provider=config_provider,
        etcd=etcd,
        db=database_engine,
        valkey_stat=valkey_clients.stat,
    )
    return ManagerAdminProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    error_log_processors: ErrorLogProcessors,
    manager_admin_processors: ManagerAdminProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for operations-domain tests."""
    return [
        register_error_log_routes(ErrorLogHandler(error_log=error_log_processors), route_deps),
        register_manager_api_routes(
            ManagerHandler(manager_admin=manager_admin_processors), route_deps
        ),
    ]


@pytest.fixture()
async def agent_fixture(
    db_engine: SAEngine,
    scaling_group_fixture: str,
) -> AsyncIterator[str]:
    """Insert a test agent record and yield its ID."""
    agent_id = f"i-test-agent-{secrets.token_hex(4)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(agents).values(
                id=agent_id,
                region="local",
                scaling_group=scaling_group_fixture,
                available_slots=ResourceSlot(),
                occupied_slots=ResourceSlot(),
                addr="127.0.0.1:6001",
                version="test",
                architecture="x86_64",
            )
        )
    yield agent_id


@pytest.fixture(autouse=True)
async def _cleanup_side_effects(
    db_engine: SAEngine,
    server: Any,
) -> AsyncIterator[None]:
    """Clean error_logs and agents tables after each test.

    Depends on ``server`` to ensure teardown runs before user/scaling-group
    fixture teardowns, which would otherwise hit FK violations.
    """
    yield
    async with db_engine.begin() as conn:
        await conn.execute(sa.delete(error_logs))
        await conn.execute(sa.delete(agents))
