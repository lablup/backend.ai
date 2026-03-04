from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.fair_share.handler import FairShareAPIHandler
from ai.backend.manager.api.rest.fair_share.registry import register_fair_share_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.scaling_group import sgroups_for_groups


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for fair-share-domain tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(processors=mock_processors), route_deps),
        register_fair_share_routes(FairShareAPIHandler(mock_processors), route_deps),
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
