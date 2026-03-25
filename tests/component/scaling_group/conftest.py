from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.appproxy.coordinator.api.types import AppProxyStatusResponse
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.scaling_group.handler import ScalingGroupHandler
from ai.backend.manager.api.rest.scaling_group.registry import register_scaling_group_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.models.scaling_group import scaling_groups, sgroups_for_domains
from ai.backend.manager.models.scaling_group.row import ScalingGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scaling_group.repository import ScalingGroupRepository
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


@pytest.fixture()
def mock_appproxy_client_pool() -> AppProxyClientPool:
    pool = MagicMock(spec=AppProxyClientPool)
    mock_client = AsyncMock()
    mock_client.fetch_status.return_value = AppProxyStatusResponse(
        api_version="v2",
        advertise_address="http://mock-wsproxy:10200",
    )
    pool.load_client.return_value = mock_client
    return pool


@pytest.fixture()
def scaling_group_processors(
    database_engine: ExtendedAsyncSAEngine,
    mock_appproxy_client_pool: AppProxyClientPool,
) -> ScalingGroupProcessors:
    repo = ScalingGroupRepository(database_engine)
    service = ScalingGroupService(repo, appproxy_client_pool=mock_appproxy_client_pool)
    return ScalingGroupProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    scaling_group_processors: ScalingGroupProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for scaling-group tests."""
    return [
        register_scaling_group_routes(
            ScalingGroupHandler(scaling_group=scaling_group_processors), route_deps
        ),
    ]


@pytest.fixture()
async def scaling_group_with_wsproxy(
    db_engine: SAEngine,
    domain_fixture: str,
) -> AsyncIterator[str]:
    """Insert a scaling group with wsproxy_addr configured; yield the name."""
    sgroup_name = f"sgroup-wsproxy-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(scaling_groups).values(
                name=sgroup_name,
                description=f"Test scaling group with wsproxy {sgroup_name}",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
                wsproxy_addr="http://mock-wsproxy:10200",
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
            sgroups_for_domains.delete().where(
                sgroups_for_domains.c.scaling_group == sgroup_name
            )
        )
        await conn.execute(scaling_groups.delete().where(scaling_groups.c.name == sgroup_name))
