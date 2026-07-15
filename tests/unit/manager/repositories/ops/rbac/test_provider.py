"""Integration tests for RBAC ops scope creation with a real database.

Verify that ``create_scope`` / ``bulk_create_scopes`` materialize both the virtual
scope node and the scope-as-entity membership in the scope's own virtual scope.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.base import Creator, CreatorSpec
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider, ScopeCreation
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
    ScalingGroupForDomainRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
)

_TEST_SCOPE_TYPE = ScopeType("test-scope")
_TEST_ENTITY_TYPE = EntityType("test-scope")


# =============================================================================
# Test Row Model (synthetic owner scope entity)
# =============================================================================


class OpsRBACScopeRow(Base):  # type: ignore[misc]
    """Synthetic scope-entity row for RBAC ops scope-creation testing."""

    __tablename__ = "test_ops_rbac_scope"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)


@dataclass
class ScopeRowCreatorSpec(CreatorSpec[OpsRBACScopeRow]):
    scope_id: UUID
    name: str

    @override
    def build_row(self) -> OpsRBACScopeRow:
        return OpsRBACScopeRow(id=self.scope_id, name=self.name)


def make_scope_creation(scope_id: UUID, name: str) -> ScopeCreation[OpsRBACScopeRow]:
    return ScopeCreation(
        creator=Creator(spec=ScopeRowCreatorSpec(scope_id=scope_id, name=name)),
        scope=ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id),
    )


# =============================================================================
# Tables & Fixtures
# =============================================================================

_SCOPE_TABLES = [
    OpsRBACScopeRow,
    VirtualScopeRow,
    EntityMembershipRow,
]


@pytest.fixture
async def scope_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, _SCOPE_TABLES):  # type: ignore[arg-type]
        yield


@pytest.fixture
def provider(database_connection: ExtendedAsyncSAEngine) -> RBACOpsProvider:
    return RBACOpsProvider(database_connection)


@dataclass
class SingleScopeContext:
    scope_id: UUID
    creation: ScopeCreation[OpsRBACScopeRow]


@dataclass
class BulkScopeContext:
    scope_ids: list[UUID]
    creations: list[ScopeCreation[OpsRBACScopeRow]]


@pytest.fixture
def single_scope() -> SingleScopeContext:
    scope_id = uuid.uuid4()
    return SingleScopeContext(
        scope_id=scope_id,
        creation=make_scope_creation(scope_id, "scope-1"),
    )


@pytest.fixture
def bulk_scopes() -> BulkScopeContext:
    scope_ids = [uuid.uuid4() for _ in range(3)]
    return BulkScopeContext(
        scope_ids=scope_ids,
        creations=[
            make_scope_creation(scope_id, f"scope-{i}") for i, scope_id in enumerate(scope_ids)
        ],
    )


# =============================================================================
# Tests
# =============================================================================


class TestScopeCreationVirtualScope:
    """create_scope / bulk_create_scopes materialize the VS node and self-membership."""

    async def test_create_scope_adds_virtual_scope_and_self_membership(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_tables: None,
        single_scope: SingleScopeContext,
    ) -> None:
        """create_scope creates the VS node and registers the scope in its own VS."""
        scope_id = single_scope.scope_id

        async with provider.write_ops() as w:
            result = await w.create_scope(single_scope.creation)

        assert result.row.id == scope_id

        async with database_connection.begin_session_read_committed() as sess:
            vs_rows = (
                (
                    await sess.execute(
                        sa.select(VirtualScopeRow).where(VirtualScopeRow.scope_id == scope_id)
                    )
                )
                .scalars()
                .all()
            )
            membership_rows = (await sess.execute(sa.select(EntityMembershipRow))).scalars().all()

        assert len(vs_rows) == 1
        vs = vs_rows[0]
        assert vs.scope_type == _TEST_SCOPE_TYPE
        assert vs.scope_id == scope_id

        assert len(membership_rows) == 1
        membership = membership_rows[0]
        assert membership.virtual_scope_id == vs.id
        assert membership.entity_type == _TEST_ENTITY_TYPE
        assert membership.entity_id == scope_id
        assert membership.permission_cap is None

    async def test_bulk_create_scopes_adds_vs_and_self_membership_per_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_tables: None,
        bulk_scopes: BulkScopeContext,
    ) -> None:
        """bulk_create_scopes creates one VS node and one self-membership per scope."""
        scope_ids = bulk_scopes.scope_ids

        async with provider.write_ops() as w:
            await w.bulk_create_scopes(bulk_scopes.creations)

        async with database_connection.begin_session_read_committed() as sess:
            vs_rows = (await sess.execute(sa.select(VirtualScopeRow))).scalars().all()
            membership_rows = (await sess.execute(sa.select(EntityMembershipRow))).scalars().all()

        assert {vs.scope_id for vs in vs_rows} == set(scope_ids)
        vs_by_scope = {vs.scope_id: vs for vs in vs_rows}

        assert len(membership_rows) == 3
        for membership in membership_rows:
            assert membership.entity_type == _TEST_ENTITY_TYPE
            assert membership.entity_id in scope_ids
            assert membership.virtual_scope_id == vs_by_scope[membership.entity_id].id
            assert membership.permission_cap is None
