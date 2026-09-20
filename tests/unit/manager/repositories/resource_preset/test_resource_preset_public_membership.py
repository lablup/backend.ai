"""A preset bound to no resource group is offered to every user, so it belongs to the
`public` scope. Held against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.creators import ResourcePresetCreator
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_preset.updaters import (
    ResourcePresetResourceGroupUpdater,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.resource_preset.db_source.db_source import (
    ResourcePresetDBSource,
)
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        global_entity_ids,
        [
            ResourcePresetRow,
            VirtualEntityRow,
            ScopeBindingRow,
            EntityMembershipRow,
            EntityMembershipCapRow,
            EntityMembershipFieldRow,
        ],
    ):
        yield global_entity_ids


@pytest.fixture
def db_source(db: ExtendedAsyncSAEngine) -> ResourcePresetDBSource:
    return ResourcePresetDBSource(db, ShareOpsProvider(db))


async def _create(
    db_source: ResourcePresetDBSource, *, resource_group_name: str | None
) -> ResourcePresetData:
    return await db_source.create_preset(
        ResourcePresetCreator(
            name=f"preset-{uuid.uuid4().hex[:8]}",
            resource_slots=ResourceSlot({"cpu": "1", "mem": "1G"}),
            shared_memory=None,
            resource_group_name=resource_group_name,
        )
    )


async def _in_public(db: ExtendedAsyncSAEngine, entity: EntityIdentifier) -> bool:
    """Whether `public` both owns and governs the entity."""
    node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == entity.entity_type(),
            VirtualEntityRow.entity_id == entity,
        )
        .scalar_subquery()
    )
    public_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == "global",
            VirtualEntityRow.entity_id == global_entity_id(GlobalEntityName.PUBLIC),
        )
        .scalar_subquery()
    )
    async with db.begin_readonly_session() as session:
        owned = await session.scalar(
            sa.select(EntityMembershipRow.id).where(
                EntityMembershipRow.virtual_entity_id == public_node,
                EntityMembershipRow.member_entity_id == node,
                EntityMembershipRow.capped.is_(False),
            )
        )
        governed = await session.scalar(
            sa.select(ScopeBindingRow.virtual_entity_id).where(
                ScopeBindingRow.virtual_entity_id == node,
                ScopeBindingRow.scope_entity_id == public_node,
            )
        )
    return owned is not None and governed is not None


class TestResourcePresetPublicMembership:
    async def test_a_preset_without_a_resource_group_is_created_in_public(
        self, db: ExtendedAsyncSAEngine, db_source: ResourcePresetDBSource
    ) -> None:
        preset = await _create(db_source, resource_group_name=None)

        assert await _in_public(db, ResourcePresetID(preset.id))

    async def test_a_preset_bound_to_a_resource_group_is_not(
        self, db: ExtendedAsyncSAEngine, db_source: ResourcePresetDBSource
    ) -> None:
        preset = await _create(db_source, resource_group_name="some-group")

        assert not await _in_public(db, ResourcePresetID(preset.id))

    async def test_binding_it_to_a_resource_group_takes_it_out(
        self, db: ExtendedAsyncSAEngine, db_source: ResourcePresetDBSource
    ) -> None:
        preset = await _create(db_source, resource_group_name=None)

        written = await db_source.set_preset_resource_group(
            ResourcePresetResourceGroupUpdater(
                preset_id=ResourcePresetID(preset.id), resource_group_name="some-group"
            )
        )

        assert written.resource_group_name == "some-group"
        assert not await _in_public(db, ResourcePresetID(preset.id))

    async def test_unbinding_it_takes_it_in(
        self, db: ExtendedAsyncSAEngine, db_source: ResourcePresetDBSource
    ) -> None:
        preset = await _create(db_source, resource_group_name="some-group")

        written = await db_source.set_preset_resource_group(
            ResourcePresetResourceGroupUpdater(
                preset_id=ResourcePresetID(preset.id), resource_group_name=None
            )
        )

        assert written.resource_group_name is None
        assert await _in_public(db, ResourcePresetID(preset.id))
