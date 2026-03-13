from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.fair_share.handler import FairShareAPIHandler
from ai.backend.manager.api.rest.fair_share.registry import register_fair_share_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.scaling_group import sgroups_for_groups
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.fair_share.repository import FairShareRepository
from ai.backend.manager.repositories.resource_usage_history.repository import (
    ResourceUsageHistoryRepository,
)
from ai.backend.manager.repositories.scaling_group.repository import ScalingGroupRepository
from ai.backend.manager.services.fair_share.processors import FairShareProcessors
from ai.backend.manager.services.fair_share.service import FairShareService
from ai.backend.manager.services.resource_usage.processors import ResourceUsageProcessors
from ai.backend.manager.services.resource_usage.service import ResourceUsageService
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


@pytest.fixture()
def fair_share_processors(database_engine: ExtendedAsyncSAEngine) -> FairShareProcessors:
    repo = FairShareRepository(database_engine)
    service = FairShareService(repo)
    return FairShareProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def resource_usage_processors(database_engine: ExtendedAsyncSAEngine) -> ResourceUsageProcessors:
    repo = ResourceUsageHistoryRepository(database_engine)
    service = ResourceUsageService(repo)
    return ResourceUsageProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def scaling_group_processors(database_engine: ExtendedAsyncSAEngine) -> ScalingGroupProcessors:
    repo = ScalingGroupRepository(database_engine)
    service = ScalingGroupService(repo, appproxy_client_pool=None)
    return ScalingGroupProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    fair_share_processors: FairShareProcessors,
    resource_usage_processors: ResourceUsageProcessors,
    scaling_group_processors: ScalingGroupProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for fair-share-domain tests."""
    return [
        register_fair_share_routes(
            FairShareAPIHandler(
                fair_share=fair_share_processors,
                resource_usage=resource_usage_processors,
                scaling_group=scaling_group_processors,
            ),
            route_deps,
        ),
    ]


@pytest.fixture()
async def group_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
    scaling_group_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test group with scaling-group association for fair-share tests."""
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
        await conn.execute(
            sa.insert(sgroups_for_groups).values(
                scaling_group=scaling_group_fixture,
                group=group_id,
            )
        )
    yield group_id
    async with db_engine.begin() as conn:
        await conn.execute(
            sgroups_for_groups.delete().where(sgroups_for_groups.c.group == group_id)
        )
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id))
