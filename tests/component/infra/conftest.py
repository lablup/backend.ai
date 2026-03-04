from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.etcd.registry import register_etcd_routes
from ai.backend.manager.api.rest.resource.registry import register_resource_routes
from ai.backend.manager.api.rest.scaling_group.registry import register_scaling_group_routes
from ai.backend.manager.api.rest.types import ModuleRegistrar
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow


@pytest.fixture()
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for infra-domain tests."""
    return [
        register_auth_routes,
        register_etcd_routes,
        register_resource_routes,
        register_scaling_group_routes,
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
