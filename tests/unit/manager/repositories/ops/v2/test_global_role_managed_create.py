"""Domain and resource group creators through the role-managed entity path: each row gets
its scope's preset roles and is owned and governed by the `global` scope."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy import Table
from sqlalchemy.orm import aliased

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.rbac_models import RoleRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_group.creators import ResourceGroupCreator
from ai.backend.manager.models.specs.creator import RoleManagedEntityCreator
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
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    ResourceGroupRow,
    RolePresetRow,
    RolePermissionPresetRow,
    RoleRow,
    PermissionRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityLabelRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
]

_CASES = [
    pytest.param(DomainEntityType(), DomainCreator(name="alpha"), id="domain"),
    pytest.param(
        ResourceGroupEntityType(),
        ResourceGroupCreator(name="alpha", driver="static", scheduler="fifo"),
        id="resource_group",
    ),
]


@pytest.fixture
async def db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, _TABLES):
        yield global_entity_ids


@pytest.fixture
def repository(db: ExtendedAsyncSAEngine) -> OpsRepository[Any]:
    return OpsRepository(V2DBOpsProvider(db))


def _node_of(entity_type: str, entity_id: uuid.UUID) -> sa.ScalarSelect[VirtualEntityID]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == entity_type,
            VirtualEntityRow.entity_id == entity_id,
        )
        .scalar_subquery()
    )


async def _add_preset(db: ExtendedAsyncSAEngine, scope_type: EntityType) -> uuid.UUID:
    async with db.begin_session() as session:
        preset = RolePresetRow(
            name="member", scope_type=scope_type, auto_assign=False, deleted=False
        )
        session.add(preset)
        await session.flush()
        return preset.id


async def _global_owns_and_governs(
    db: ExtendedAsyncSAEngine, entity_type: str, entity_id: uuid.UUID
) -> bool:
    global_node = _node_of(GlobalEntityType(), global_entity_id(GlobalEntityName.GLOBAL))
    entity_node = _node_of(entity_type, entity_id)
    async with db.begin_readonly_session() as session:
        owns = await session.scalar(
            sa.select(
                sa.exists().where(
                    EntityMembershipRow.virtual_entity_id == global_node,
                    EntityMembershipRow.member_entity_id == entity_node,
                    EntityMembershipRow.capped.is_(False),
                )
            )
        )
        governs = await session.scalar(
            sa.select(
                sa.exists().where(
                    ScopeBindingRow.virtual_entity_id == entity_node,
                    ScopeBindingRow.scope_entity_id == global_node,
                )
            )
        )
    return bool(owns) and bool(governs)


async def _preset_role_ids(
    db: ExtendedAsyncSAEngine, entity_type: str, entity_id: uuid.UUID, preset_id: uuid.UUID
) -> list[uuid.UUID]:
    """The roles from the preset enrolled in the entity's virtual entity."""
    role_node = aliased(VirtualEntityRow)
    async with db.begin_readonly_session() as session:
        return list(
            (
                await session.scalars(
                    sa.select(RoleRow.id)
                    .join(role_node, role_node.entity_id == RoleRow.id)
                    .join(
                        EntityMembershipRow,
                        EntityMembershipRow.member_entity_id == role_node.id,
                    )
                    .where(
                        EntityMembershipRow.virtual_entity_id == _node_of(entity_type, entity_id),
                        role_node.entity_type == RoleEntityType(),
                        RoleRow.role_preset_id == preset_id,
                    )
                )
            ).all()
        )


class TestGlobalRoleManagedCreate:
    @pytest.mark.parametrize(("entity_type", "creator"), _CASES)
    async def test_create_provisions_preset_roles_and_joins_the_global_scope(
        self,
        db: ExtendedAsyncSAEngine,
        repository: OpsRepository[Any],
        entity_type: EntityType,
        creator: RoleManagedEntityCreator[Any, Any],
    ) -> None:
        preset_id = await _add_preset(db, entity_type)

        data = await repository.create_role_managed_entity(creator)

        assert await _global_owns_and_governs(db, entity_type, data.id)
        assert len(await _preset_role_ids(db, entity_type, data.id, preset_id)) == 1
