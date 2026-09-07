"""Integration tests for the RBAC ops provider (RBACWriteOps) with a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import (
    EntityType as VirtualEntityEntityType,
)
from ai.backend.common.data.entity.types import (
    ScopeRef,
    ScopeType,
)
from ai.backend.common.data.permission.types import (
    RBACElementType,
)
from ai.backend.common.data.permission.types import ScopeType as PermissionScopeType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
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
from ai.backend.manager.repositories.ops.rbac.provider import (
    RBACOpsProvider,
)
from ai.backend.testutils.db import with_tables

# ORM cluster registration: create()/flush triggers configure_mappers() over the whole
# registry, and importing the RBAC ops provider registers RoleRow/UserRoleRow whose
# string relationships resolve against these rows. _ORM_CLUSTER keeps them live.
_ORM_CLUSTER = (
    AgentRow,
    AssociationScopesEntitiesRow,
    DomainRow,
    KeyPairRow,
    KeyPairResourcePolicyRow,
    ObjectPermissionRow,
    PermissionRow,
    RoleRow,
    ResourceGroupForDomainRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
)

# A scope that carries roles must name a type the permission layer knows.
_TEST_SCOPE_TYPE = ScopeType(VirtualEntityEntityType(PermissionScopeType.PROJECT.value))
_TEST_ENTITY_TYPE = VirtualEntityEntityType(PermissionScopeType.PROJECT.value)
_TEST_MEMBER_ENTITY_TYPE = VirtualEntityEntityType(RBACElementType.USER.value)
_TEST_MEMBER_SCOPE_TYPE = ScopeType(VirtualEntityEntityType(RBACElementType.USER.value))

_USER_SCOPE_ID = str(uuid.uuid4())
_USER_SCOPE_REF = RBACElementRef(RBACElementType.USER, _USER_SCOPE_ID)
_PROJECT_SCOPE_ID = str(uuid.uuid4())
_PROJECT_SCOPE_REF = RBACElementRef(RBACElementType.PROJECT, _PROJECT_SCOPE_ID)


# =============================================================================
# Test Row Models
# =============================================================================


class OpsRBACScopeRow(Base):
    """Synthetic scope-entity row for RBAC ops scope-creation testing."""

    __tablename__ = "test_ops_rbac_scope"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)


async def _entity_by_node(sess: SASession) -> dict[UUID, UUID]:
    """Virtual entity id -> the entity id it stands for."""
    rows = (await sess.execute(sa.select(VirtualEntityRow.id, VirtualEntityRow.entity_id))).all()
    return {row.id: row.entity_id for row in rows}


_SCOPE_TABLES = [
    OpsRBACScopeRow,
    VirtualEntityRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
    ScopeBindingRow,
    EntityLabelRow,
]


@pytest.fixture
async def scope_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, _SCOPE_TABLES):
        yield


@pytest.fixture
def provider(database_connection: ExtendedAsyncSAEngine) -> RBACOpsProvider:
    return RBACOpsProvider(database_connection)


class TestEnsureScope:
    """ensure_scope backfills the virtual entity, self-membership, and self binding for an
    already-created scope, without creating the real scope row."""

    async def test_ensure_scope_adds_vs_membership_and_self_binding_without_real_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_tables: None,
    ) -> None:
        """ensure_scope creates the virtual entity, self-membership, and self binding, and leaves
        no real scope row behind."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)

        async with database_connection.begin_session_read_committed() as sess:
            ve_rows = (await sess.execute(sa.select(VirtualEntityRow))).scalars().all()
            membership_rows = (await sess.execute(sa.select(EntityMembershipRow))).scalars().all()
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            real_row_count = await sess.scalar(
                sa.select(sa.func.count()).select_from(OpsRBACScopeRow)
            )

        assert len(ve_rows) == 1
        ve = ve_rows[0]
        assert ve.entity_id == scope_id

        assert len(membership_rows) == 1
        assert membership_rows[0].virtual_entity_id == ve.id
        assert membership_rows[0].member_entity_id == ve.id

        assert len(binding_rows) == 1
        assert binding_rows[0].virtual_entity_id == ve.id
        assert binding_rows[0].scope_entity_id == ve.id
        assert binding_rows[0].permission_cap is None

        assert real_row_count == 0

    async def test_ensure_scope_is_idempotent(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_tables: None,
    ) -> None:
        """Calling ensure_scope twice leaves exactly one virtual entity, membership, and binding."""
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(scope)

        async with database_connection.begin_session_read_committed() as sess:
            ve_count = await sess.scalar(sa.select(sa.func.count()).select_from(VirtualEntityRow))
            membership_count = await sess.scalar(
                sa.select(sa.func.count()).select_from(EntityMembershipRow)
            )
            binding_count = await sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeBindingRow)
            )

        assert ve_count == 1
        assert membership_count == 1
        assert binding_count == 1
