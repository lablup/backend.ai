"""A preset bound to no resource group is offered to every user, so it belongs to the
`public` scope; one bound to a resource group belongs to that group. Held against a real
database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
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

GROUP_NAME = "some-group"
OTHER_GROUP_NAME = "other-group"


@pytest.fixture
async def db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        global_entity_ids,
        [
            ResourceGroupRow,
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
async def resource_groups(db: ExtendedAsyncSAEngine) -> dict[str, ResourceGroupID]:
    """The two groups a preset may be bound to, each with its node in the graph."""
    ids: dict[str, ResourceGroupID] = {}
    async with db.begin_session() as session:
        for name in (GROUP_NAME, OTHER_GROUP_NAME):
            row = ResourceGroupRow(
                name=name,
                description=f"Test scaling group {name}",
                is_active=True,
                is_public=True,
                created_at=datetime.now(tz=UTC),
                wsproxy_addr=None,
                wsproxy_api_token=None,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
                use_host_network=False,
            )
            session.add(row)
            await session.flush()
            ids[name] = row.id
            session.add(VirtualEntityRow(entity_type="resource_group", entity_id=row.id))
        await session.commit()
    return ids


@pytest.fixture
def db_source(db: ExtendedAsyncSAEngine) -> ResourcePresetDBSource:
    return ResourcePresetDBSource(db, ShareOpsProvider(db))


async def _create(
    db_source: ResourcePresetDBSource,
    *,
    resource_group_name: str | None,
    resource_group_id: ResourceGroupID | None = None,
) -> ResourcePresetData:
    return await db_source.create_preset(
        ResourcePresetCreator(
            name=f"preset-{uuid.uuid4().hex[:8]}",
            resource_slots=ResourceSlot({"cpu": "1", "mem": "1G"}),
            shared_memory=None,
            resource_group_name=resource_group_name,
            resource_group_id=resource_group_id,
        )
    )


def _node(entity: EntityIdentifier) -> sa.ScalarSelect[VirtualEntityID]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == entity.entity_type(),
            VirtualEntityRow.entity_id == entity,
        )
        .scalar_subquery()
    )


async def _belongs_to(
    db: ExtendedAsyncSAEngine, scope: EntityIdentifier, entity: EntityIdentifier
) -> bool:
    """Whether the scope both owns and governs the entity."""
    node = _node(entity)
    scope_node = _node(scope)
    async with db.begin_readonly_session() as session:
        owned = await session.scalar(
            sa.select(EntityMembershipRow.id).where(
                EntityMembershipRow.virtual_entity_id == scope_node,
                EntityMembershipRow.member_entity_id == node,
                EntityMembershipRow.capped.is_(False),
            )
        )
        governed = await session.scalar(
            sa.select(ScopeBindingRow.virtual_entity_id).where(
                ScopeBindingRow.virtual_entity_id == node,
                ScopeBindingRow.scope_entity_id == scope_node,
            )
        )
    return owned is not None and governed is not None


async def _in_public(db: ExtendedAsyncSAEngine, entity: EntityIdentifier) -> bool:
    return await _belongs_to(db, global_entity_id(GlobalEntityName.PUBLIC), entity)


class TestResourcePresetMembership:
    async def test_a_preset_without_a_resource_group_is_created_in_public(
        self, db: ExtendedAsyncSAEngine, db_source: ResourcePresetDBSource
    ) -> None:
        preset = await _create(db_source, resource_group_name=None)

        assert await _in_public(db, ResourcePresetID(preset.id))

    async def test_a_preset_bound_to_a_resource_group_is_created_in_that_group(
        self,
        db: ExtendedAsyncSAEngine,
        db_source: ResourcePresetDBSource,
        resource_groups: dict[str, ResourceGroupID],
    ) -> None:
        preset = await _create(
            db_source,
            resource_group_name=GROUP_NAME,
            resource_group_id=resource_groups[GROUP_NAME],
        )

        assert not await _in_public(db, ResourcePresetID(preset.id))
        assert await _belongs_to(db, resource_groups[GROUP_NAME], ResourcePresetID(preset.id))

    async def test_binding_it_to_a_resource_group_moves_it_there(
        self,
        db: ExtendedAsyncSAEngine,
        db_source: ResourcePresetDBSource,
        resource_groups: dict[str, ResourceGroupID],
    ) -> None:
        preset = await _create(db_source, resource_group_name=None)

        written = await db_source.set_preset_resource_group(
            ResourcePresetResourceGroupUpdater(
                preset_id=ResourcePresetID(preset.id), resource_group_name=GROUP_NAME
            )
        )

        assert written.resource_group_name == GROUP_NAME
        assert not await _in_public(db, ResourcePresetID(preset.id))
        assert await _belongs_to(db, resource_groups[GROUP_NAME], ResourcePresetID(preset.id))

    async def test_rebinding_it_leaves_the_group_it_was_in(
        self,
        db: ExtendedAsyncSAEngine,
        db_source: ResourcePresetDBSource,
        resource_groups: dict[str, ResourceGroupID],
    ) -> None:
        preset = await _create(
            db_source,
            resource_group_name=GROUP_NAME,
            resource_group_id=resource_groups[GROUP_NAME],
        )

        await db_source.set_preset_resource_group(
            ResourcePresetResourceGroupUpdater(
                preset_id=ResourcePresetID(preset.id), resource_group_name=OTHER_GROUP_NAME
            )
        )

        assert not await _belongs_to(db, resource_groups[GROUP_NAME], ResourcePresetID(preset.id))
        assert await _belongs_to(db, resource_groups[OTHER_GROUP_NAME], ResourcePresetID(preset.id))

    async def test_unbinding_it_takes_it_in(
        self,
        db: ExtendedAsyncSAEngine,
        db_source: ResourcePresetDBSource,
        resource_groups: dict[str, ResourceGroupID],
    ) -> None:
        preset = await _create(
            db_source,
            resource_group_name=GROUP_NAME,
            resource_group_id=resource_groups[GROUP_NAME],
        )

        written = await db_source.set_preset_resource_group(
            ResourcePresetResourceGroupUpdater(
                preset_id=ResourcePresetID(preset.id), resource_group_name=None
            )
        )

        assert written.resource_group_name is None
        assert await _in_public(db, ResourcePresetID(preset.id))
        assert not await _belongs_to(db, resource_groups[GROUP_NAME], ResourcePresetID(preset.id))
