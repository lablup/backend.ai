"""Integration tests for the RBAC ops provider (RBACWriteOps) with a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.types import (
    EntityRef,
    ScopeRef,
    ScopeType,
)
from ai.backend.common.data.entity.types import (
    EntityType as VirtualEntityEntityType,
)
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.common.data.permission.types import (
    EntityType,
    Permission,
    RBACElementType,
    RelationType,
)
from ai.backend.common.data.permission.types import ScopeType as PermissionScopeType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.permission import VirtualEntityNotFound
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
    EntityMembersAddition,
    RBACOpsProvider,
    ScopeMember,
    ScopeUserMember,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

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


async def _member_ids_of(
    sess: SASession, virtual_entity_id: UUID, *, any_type: bool = False
) -> set[UUID]:
    """Entity ids enrolled in the virtual entity; members of ``_TEST_MEMBER_ENTITY_TYPE``
    unless ``any_type``."""
    query = (
        sa.select(VirtualEntityRow.entity_id)
        .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
        .where(EntityMembershipRow.virtual_entity_id == virtual_entity_id)
    )
    if not any_type:
        query = query.where(VirtualEntityRow.entity_type == _TEST_MEMBER_ENTITY_TYPE)
    return set((await sess.scalars(query)).all())


@dataclass
class StubMember(ScopeMember):
    member_id: UUID
    role_user: UserID | None = None
    entity_type: VirtualEntityEntityType = _TEST_MEMBER_ENTITY_TYPE
    cap: Permission | None = None

    @override
    def entity_ref(self) -> EntityRef:
        return EntityRef(entity_type=self.entity_type, entity_id=self.member_id)

    @override
    def assign_role_on(self) -> UserID | None:
        return self.role_user

    @override
    def permission_cap(self, scope: ScopeRef) -> Permission | None:
        return self.cap


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


_ENTITY_MEMBER_TABLES = [
    VirtualEntityRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
    ScopeBindingRow,
    AssociationScopesEntitiesRow,
]


@pytest.fixture
async def entity_member_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, _ENTITY_MEMBER_TABLES):
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


class TestAddBulkMembers:
    """add_bulk_members enrolls each member into the scope's virtual entity with its scope
    association, and leaves the member's own virtual entity untouched — the scope reaches the
    member entities, not what they own."""

    async def test_writes_membership_and_association_without_binding(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """Each member gets membership and association, and no binding is written into
        its own virtual entity — nor a reverse binding in the scope's virtual entity."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        member_ids = [uuid.uuid4(), uuid.uuid4()]

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            for mid in member_ids:
                await w.ensure_scope(ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=mid))
            await w.add_bulk_members(
                EntityMembersAddition(
                    scope=scope,
                    members=[StubMember(member_id=mid, cap=Permission.READ) for mid in member_ids],
                ),
            )

        async with database_connection.begin_session_read_committed() as sess:
            ve_rows = (await sess.execute(sa.select(VirtualEntityRow))).scalars().all()
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            ve_by_scope = {ve.entity_id: ve.id for ve in ve_rows}
            membership_ids = await _member_ids_of(sess, ve_by_scope[scope_id])
            assoc_ids = set(
                (
                    await sess.scalars(
                        sa.select(AssociationScopesEntitiesRow.entity_id).where(
                            AssociationScopesEntitiesRow.scope_id == str(scope_id),
                            AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                        )
                    )
                ).all()
            )

        assert membership_ids == set(member_ids)
        assert assoc_ids == {str(mid) for mid in member_ids}

        for mid in member_ids:
            member_bindings = {
                b.scope_entity_id for b in binding_rows if b.virtual_entity_id == ve_by_scope[mid]
            }
            assert member_bindings == {ve_by_scope[mid]}  # self binding only
        scope_ve_bindings = {
            b.scope_entity_id for b in binding_rows if b.virtual_entity_id == ve_by_scope[scope_id]
        }
        assert scope_ve_bindings == {ve_by_scope[scope_id]}  # self binding only

    async def test_member_without_own_virtual_entity_fails(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """The membership edge names the member's own virtual entity, so a member without
        one raises VirtualEntityNotFound and nothing is written."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        member_id = uuid.uuid4()

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)

        with pytest.raises(VirtualEntityNotFound):
            async with provider.write_ops() as w:
                await w.add_bulk_members(
                    EntityMembersAddition(scope=scope, members=[StubMember(member_id=member_id)])
                )

        async with database_connection.begin_session_read_committed() as sess:
            scope_ve = (
                await sess.execute(
                    sa.select(VirtualEntityRow).where(VirtualEntityRow.entity_id == scope_id)
                )
            ).scalar_one()
            membership_ids = await _member_ids_of(sess, scope_ve.id)
            assoc_count = await sess.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(AssociationScopesEntitiesRow.entity_id == str(member_id))
            )

        assert membership_ids == set()
        assert assoc_count == 0

    async def test_readd_is_idempotent(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """Re-adding the same member is a no-op — no duplicate membership or
        association."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        member_id = uuid.uuid4()
        member_scope = ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=member_id)
        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(member_scope)
            await w.add_bulk_members(
                EntityMembersAddition(
                    scope=scope,
                    members=[StubMember(member_id=member_id, cap=Permission.READ)],
                )
            )
            await w.add_bulk_members(
                EntityMembersAddition(
                    scope=scope,
                    members=[StubMember(member_id=member_id, cap=Permission.full())],
                )
            )

        async with database_connection.begin_session_read_committed() as sess:
            scope_ve = (
                await sess.execute(
                    sa.select(VirtualEntityRow).where(VirtualEntityRow.entity_id == scope_id)
                )
            ).scalar_one()
            membership_rows = (
                (
                    await sess.execute(
                        sa.select(EntityMembershipRow).where(
                            EntityMembershipRow.virtual_entity_id == scope_ve.id
                        )
                    )
                )
                .scalars()
                .all()
            )
            entity_by_node = await _entity_by_node(sess)
            caps_by_entity = {
                entity_by_node[m.member_entity_id]: await VirtualEntitySeeder().edge_cap(
                    sess, m.virtual_entity_id, m.member_entity_id
                )
                for m in membership_rows
            }
            assoc_count = await sess.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(AssociationScopesEntitiesRow.entity_id == str(member_id))
            )

        # the scope's self membership and the member's
        assert len(membership_rows) == 2
        assert assoc_count == 1
        assert caps_by_entity == {
            scope_id: None,  # self membership
            member_id: Permission.READ,
        }

    async def test_empty_members_is_noop(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """An empty member collection writes nothing."""
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.add_bulk_members(EntityMembersAddition(scope=scope, members=[]))

        async with database_connection.begin_session_read_committed() as sess:
            binding_count = await sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeBindingRow)
            )

        assert binding_count == 1  # the self binding from ensure_scope


class TestUserRosterEnrollment:
    """A user joins a scope's roster only: the enrollment row carries the scope kind's
    constant cap, and nothing is bound into the user's own virtual entity."""

    @pytest.fixture
    async def roster_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[None, None]:
        async with with_tables(
            database_connection,
            [
                *_ENTITY_MEMBER_TABLES,
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
            ],
        ):
            yield

    @pytest.mark.parametrize(
        ("scope_type", "expected_cap"),
        [
            pytest.param(PROJECT_SCOPE_TYPE, Permission.READ, id="project-capped-to-read"),
            pytest.param(DOMAIN_SCOPE_TYPE, None, id="domain-uncapped"),
        ],
    )
    async def test_enrollment_carries_the_scope_kinds_cap(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        roster_tables: None,
        scope_type: ScopeType,
        expected_cap: Permission | None,
    ) -> None:
        scope = ScopeRef(scope_type=scope_type, scope_id=uuid.uuid4())
        user_id = UserID(uuid.uuid4())
        user_scope = ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=user_id)

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(user_scope)
            await w.add_bulk_members(
                EntityMembersAddition(scope=scope, members=[ScopeUserMember(user_id=user_id)])
            )

        async with database_connection.begin_session_read_committed() as sess:
            ve_by_scope = {
                ve.entity_id: ve.id
                for ve in (await sess.execute(sa.select(VirtualEntityRow))).scalars().all()
            }
            cap = await VirtualEntitySeeder().edge_cap(
                sess, ve_by_scope[scope.scope_id], ve_by_scope[user_id]
            )
            user_vs_bindings = {
                b.scope_entity_id
                for b in (
                    await sess.execute(
                        sa.select(ScopeBindingRow).where(
                            ScopeBindingRow.virtual_entity_id == ve_by_scope[user_id]
                        )
                    )
                )
                .scalars()
                .all()
            }

        assert cap == expected_cap
        assert user_vs_bindings == {ve_by_scope[user_id]}  # self binding only


class TestAddBulkInheritingMembers:
    """add_bulk_inheriting_members writes everything add_bulk_members does and additionally binds
    the scope into the member's own virtual entity — never the reverse binding."""

    async def test_writes_membership_association_and_binding(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """Each member gets membership, association, and the scope's uncapped binding
        in its own virtual entity — and no reverse binding in the scope's virtual entity."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        member_ids = [uuid.uuid4(), uuid.uuid4()]

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            for mid in member_ids:
                await w.ensure_scope(ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=mid))
            await w.add_bulk_inheriting_members(
                EntityMembersAddition(
                    scope=scope,
                    members=[StubMember(member_id=mid, cap=Permission.READ) for mid in member_ids],
                ),
            )

        async with database_connection.begin_session_read_committed() as sess:
            ve_rows = (await sess.execute(sa.select(VirtualEntityRow))).scalars().all()
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            ve_by_scope = {ve.entity_id: ve.id for ve in ve_rows}
            membership_ids = await _member_ids_of(sess, ve_by_scope[scope_id])
            assoc_ids = set(
                (
                    await sess.scalars(
                        sa.select(AssociationScopesEntitiesRow.entity_id).where(
                            AssociationScopesEntitiesRow.scope_id == str(scope_id),
                            AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                        )
                    )
                ).all()
            )

        assert membership_ids == set(member_ids)
        assert assoc_ids == {str(mid) for mid in member_ids}

        for mid in member_ids:
            member_bindings = {
                b.scope_entity_id: b.permission_cap
                for b in binding_rows
                if b.virtual_entity_id == ve_by_scope[mid]
            }
            assert member_bindings == {
                ve_by_scope[mid]: None,  # self binding
                ve_by_scope[scope_id]: None,
            }
        scope_ve_bindings = {
            b.scope_entity_id for b in binding_rows if b.virtual_entity_id == ve_by_scope[scope_id]
        }
        assert scope_ve_bindings == {ve_by_scope[scope_id]}  # self binding only

    async def test_readd_is_idempotent(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """Re-adding the same member is a no-op — no duplicate membership, association,
        or binding."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        member_id = uuid.uuid4()
        member_scope = ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=member_id)
        addition = EntityMembersAddition(scope=scope, members=[StubMember(member_id=member_id)])

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(member_scope)
            await w.add_bulk_inheriting_members(addition)
            await w.add_bulk_inheriting_members(addition)

        async with database_connection.begin_session_read_committed() as sess:
            scope_ve = (
                await sess.execute(
                    sa.select(VirtualEntityRow).where(VirtualEntityRow.entity_id == scope_id)
                )
            ).scalar_one()
            member_vs = (
                await sess.execute(
                    sa.select(VirtualEntityRow).where(VirtualEntityRow.entity_id == member_id)
                )
            ).scalar_one()
            membership_count = await sess.scalar(
                sa.select(sa.func.count())
                .select_from(EntityMembershipRow)
                .where(EntityMembershipRow.virtual_entity_id == scope_ve.id)
            )
            assoc_count = await sess.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(AssociationScopesEntitiesRow.entity_id == str(member_id))
            )
            binding_rows = (
                (
                    await sess.execute(
                        sa.select(ScopeBindingRow).where(
                            ScopeBindingRow.virtual_entity_id == member_vs.id
                        )
                    )
                )
                .scalars()
                .all()
            )

        # the scope's self membership and the member's
        assert membership_count == 2
        assert assoc_count == 1
        caps_by_scope = {b.scope_entity_id: b.permission_cap for b in binding_rows}
        assert caps_by_scope == {
            member_vs.id: None,  # self binding
            scope_ve.id: None,
        }

    async def test_missing_member_vs_fails_the_whole_call(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """One member without a virtual entity raises VirtualEntityNotFound and nothing is written —
        no membership and no binding, not even for the members whose virtual entity exists."""
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())
        present_id, missing_id = uuid.uuid4(), uuid.uuid4()

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=present_id))

        with pytest.raises(VirtualEntityNotFound):
            async with provider.write_ops() as w:
                await w.add_bulk_inheriting_members(
                    EntityMembersAddition(
                        scope=scope,
                        members=[
                            StubMember(member_id=present_id),
                            StubMember(member_id=missing_id),
                        ],
                    )
                )

        async with database_connection.begin_session_read_committed() as sess:
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            membership_rows = (await sess.execute(sa.select(EntityMembershipRow))).scalars().all()
            entity_by_node = await _entity_by_node(sess)

        assert {(b.virtual_entity_id, b.scope_entity_id) for b in binding_rows} == {
            (node, node) for node in entity_by_node
        }  # self bindings only
        assert {(m.virtual_entity_id, m.member_entity_id) for m in membership_rows} == {
            (node, node) for node in entity_by_node
        }  # self memberships only
        assert set(entity_by_node.values()) == {scope.scope_id, present_id}

    async def test_empty_members_is_noop(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """An empty member collection writes nothing."""
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.add_bulk_inheriting_members(EntityMembersAddition(scope=scope, members=[]))

        async with database_connection.begin_session_read_committed() as sess:
            binding_count = await sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeBindingRow)
            )

        assert binding_count == 1  # the self binding from ensure_scope


class TestRemoveBulkMembers:
    """remove_bulk_members deletes the virtual entity membership, the scope association, and the
    scope's binding in the member's own virtual entity — and never raises for missing virtual
    scopes."""

    async def test_remove_deletes_membership_association_and_binding(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """The removed member loses all three rows — its own virtual entity keeps only the self
        binding — while the other one keeps all of them."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        removed_id, kept_id = uuid.uuid4(), uuid.uuid4()

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            for mid in (removed_id, kept_id):
                await w.ensure_scope(ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=mid))
            await w.add_bulk_inheriting_members(
                EntityMembersAddition(
                    scope=scope,
                    members=[StubMember(member_id=removed_id), StubMember(member_id=kept_id)],
                )
            )
            await w.remove_bulk_members(
                scope,
                [EntityRef(entity_type=_TEST_MEMBER_ENTITY_TYPE, entity_id=removed_id)],
            )

        async with database_connection.begin_session_read_committed() as sess:
            ve_rows = (await sess.execute(sa.select(VirtualEntityRow))).scalars().all()
            ve_by_scope = {ve.entity_id: ve.id for ve in ve_rows}
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            membership_ids = await _member_ids_of(sess, ve_by_scope[scope_id])
            assoc_ids = set(
                (
                    await sess.scalars(
                        sa.select(AssociationScopesEntitiesRow.entity_id).where(
                            AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                        )
                    )
                ).all()
            )

        assert membership_ids == {kept_id}
        assert assoc_ids == {str(kept_id)}
        removed_bindings = {
            b.scope_entity_id
            for b in binding_rows
            if b.virtual_entity_id == ve_by_scope[removed_id]
        }
        assert removed_bindings == {ve_by_scope[removed_id]}  # self binding only
        kept_bindings = {
            b.scope_entity_id for b in binding_rows if b.virtual_entity_id == ve_by_scope[kept_id]
        }
        assert kept_bindings == {ve_by_scope[kept_id], ve_by_scope[scope_id]}

    async def test_remove_without_member_self_edges_still_deletes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """A member whose node carries no self edges or binding (legacy data) still loses its
        membership and association — the removal does not raise."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        member_id = uuid.uuid4()

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)

        async with database_connection.begin_session() as sess:
            scope_ve = (
                await sess.execute(
                    sa.select(VirtualEntityRow).where(VirtualEntityRow.entity_id == scope_id)
                )
            ).scalar_one()
            member_node = VirtualEntityRow(
                entity_type=_TEST_MEMBER_ENTITY_TYPE, entity_id=member_id
            )
            sess.add(member_node)
            await sess.flush()
            sess.add(
                EntityMembershipRow(
                    virtual_entity_id=scope_ve.id,
                    member_entity_id=member_node.id,
                    capped=False,
                )
            )
            sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=PermissionScopeType(_TEST_SCOPE_TYPE),
                    scope_id=str(scope_id),
                    entity_type=EntityType.USER,
                    entity_id=str(member_id),
                    relation_type=RelationType.AUTO,
                )
            )

        async with provider.write_ops() as w:
            await w.remove_bulk_members(
                scope,
                [EntityRef(entity_type=_TEST_MEMBER_ENTITY_TYPE, entity_id=member_id)],
            )

        async with database_connection.begin_session_read_committed() as sess:
            membership_count = await sess.scalar(
                sa.select(sa.func.count())
                .select_from(EntityMembershipRow)
                .join(VirtualEntityRow, VirtualEntityRow.id == EntityMembershipRow.member_entity_id)
                .where(VirtualEntityRow.entity_id == member_id)
            )
            assoc_count = await sess.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(AssociationScopesEntitiesRow.entity_id == str(member_id))
            )

        assert membership_count == 0
        assert assoc_count == 0


# =============================================================================
# add_bulk_members_partial
# =============================================================================


class TestAddBulkMembersPartial:
    """add_bulk_members_partial isolates each member: a failed member is reported and
    rolled back while the rest are fully attached."""

    async def test_failed_member_is_isolated(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """A member whose entity type has no legacy counterpart fails alone — its
        membership is rolled back with it — while the valid member keeps all rows."""
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())
        valid = StubMember(member_id=uuid.uuid4())
        invalid = StubMember(
            member_id=uuid.uuid4(),
            entity_type=VirtualEntityEntityType("unregistered-type"),
        )

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(
                ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=valid.member_id)
            )
            await w.ensure_scope(
                ScopeRef(
                    scope_type=ScopeType(VirtualEntityEntityType("unregistered-type")),
                    scope_id=invalid.member_id,
                )
            )
            result = await w.add_bulk_members_partial(
                EntityMembersAddition(scope=scope, members=[valid, invalid])
            )

        assert result.successes == [valid]
        assert [error.member for error in result.errors] == [invalid]
        assert result.errors[0].index == 1

        async with database_connection.begin_session_read_committed() as sess:
            scope_ve = (
                await sess.execute(
                    sa.select(VirtualEntityRow).where(VirtualEntityRow.entity_id == scope.scope_id)
                )
            ).scalar_one()
            membership_ids = await _member_ids_of(sess, scope_ve.id, any_type=True)
            assoc_ids = set(
                (
                    await sess.scalars(
                        sa.select(AssociationScopesEntitiesRow.entity_id).where(
                            AssociationScopesEntitiesRow.scope_id == str(scope.scope_id)
                        )
                    )
                ).all()
            )

        assert membership_ids == {
            scope.scope_id,  # self membership
            valid.member_id,
        }
        assert assoc_ids == {str(valid.member_id)}

    async def test_member_without_own_vs_fails_alone(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """A member without a virtual entity of its own lands in the errors while the one
        with a node is enrolled, and no binding is written into that node."""
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())
        with_ve = StubMember(member_id=uuid.uuid4(), cap=Permission.READ)
        without_ve = StubMember(member_id=uuid.uuid4(), cap=Permission.READ)

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(
                ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=with_ve.member_id)
            )
            result = await w.add_bulk_members_partial(
                EntityMembersAddition(scope=scope, members=[with_ve, without_ve])
            )

        assert result.successes == [with_ve]
        assert [error.member for error in result.errors] == [without_ve]
        assert isinstance(result.errors[0].exception, VirtualEntityNotFound)

        async with database_connection.begin_session_read_committed() as sess:
            ve_rows = (await sess.execute(sa.select(VirtualEntityRow))).scalars().all()
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            ve_by_scope = {ve.entity_id: ve.id for ve in ve_rows}
            membership_ids = await _member_ids_of(sess, ve_by_scope[scope.scope_id])

        assert without_ve.member_id not in ve_by_scope
        assert membership_ids == {with_ve.member_id}
        member_bindings = {
            b.scope_entity_id
            for b in binding_rows
            if b.virtual_entity_id == ve_by_scope[with_ve.member_id]
        }
        assert member_bindings == {ve_by_scope[with_ve.member_id]}  # self only
