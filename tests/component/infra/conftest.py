from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.etcd.handler import EtcdHandler
from ai.backend.manager.api.rest.etcd.registry import register_etcd_routes
from ai.backend.manager.api.rest.resource.handler import ResourceHandler
from ai.backend.manager.api.rest.resource.registry import register_resource_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.scaling_group.handler import ScalingGroupHandler
from ai.backend.manager.api.rest.scaling_group.registry import register_scaling_group_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps, config_provider: ManagerConfigProvider
) -> list[RouteRegistry]:
    """Load only the modules required for infra-domain tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(auth=mock_processors.auth), route_deps),
        register_etcd_routes(
            EtcdHandler(
                container_registry=mock_processors.container_registry,
                etcd_config=mock_processors.etcd_config,
            ),
            route_deps,
            pidx=0,
            config_provider=config_provider,
        ),
        register_resource_routes(
            ResourceHandler(
                resource_preset=mock_processors.resource_preset,
                agent=mock_processors.agent,
                group=mock_processors.group,
                user=mock_processors.user,
                container_registry=mock_processors.container_registry,
            ),
            route_deps,
        ),
        register_scaling_group_routes(
            ScalingGroupHandler(scaling_group=mock_processors.scaling_group), route_deps
        ),
    ]


@pytest.fixture()
async def group_name_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
) -> str:
    """Query the group name from the database for the test group."""
    async with db_engine.begin() as conn:
        result = await conn.execute(
            sa.select(GroupRow.__table__.c.name).where(GroupRow.__table__.c.id == group_fixture)
        )
        row = result.first()
        assert row is not None
        return str(row[0])


@pytest.fixture()
async def resource_preset_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[dict[str, str]]:
    """Insert a test resource preset and yield its metadata.

    Used for list_presets and check_presets tests. Cleaned up after each test.
    """
    preset_id = uuid.uuid4()
    preset_name = f"test-preset-{preset_id.hex[:8]}"
    resource_slots = ResourceSlot({"cpu": "1", "mem": "1073741824"})
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ResourcePresetRow.__table__).values(
                id=preset_id,
                name=preset_name,
                resource_slots=resource_slots,
                shared_memory=None,
                scaling_group_name=None,
            )
        )
    yield {"id": str(preset_id), "name": preset_name}
    async with db_engine.begin() as conn:
        await conn.execute(
            ResourcePresetRow.__table__.delete().where(
                ResourcePresetRow.__table__.c.id == preset_id
            )
        )
