"""Integration tests for the RBAC ops provider (RBACWriteOps) with a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Collection, Sequence
from dataclasses import dataclass, field
from typing import override
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import (
    EntityRef,
    ScopeRef,
    ScopeType,
)
from ai.backend.common.data.entity.types import (
    EntityType as VirtualScopeEntityType,
)
from ai.backend.common.data.permission.types import EntityType, RBACElementType, RelationType
from ai.backend.common.data.permission.types import ScopeType as PermissionScopeType
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.permission.types import RBACElementRef
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
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.base import CreatorSpec
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.rbac.entity_purger import (
    RBACEntityPurger,
    RBACEntityPurgerSpec,
)
from ai.backend.manager.repositories.base.types import ConflictCheck
from ai.backend.manager.repositories.ops.rbac.provider import (
    EntityMembersAddition,
    RBACOpsProvider,
    ScopeCreation,
    ScopeMember,
)
from ai.backend.manager.repositories.permission_controller.role_manager import (
    ScopeSystemRoleData,
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
    ScalingGroupForDomainRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
)

# A scope that carries roles must name a type the permission layer knows; a scope merely
# bound to a virtual scope is free-form, which _TEST_BOUND_SCOPE_TYPE exercises.
_TEST_SCOPE_TYPE = ScopeType(PermissionScopeType.PROJECT.value)
_TEST_ENTITY_TYPE = VirtualScopeEntityType(PermissionScopeType.PROJECT.value)
_TEST_BOUND_SCOPE_TYPE = ScopeType("test-bound-scope")
_TEST_MEMBER_ENTITY_TYPE = VirtualScopeEntityType(RBACElementType.USER.value)

_USER_SCOPE_ID = str(uuid.uuid4())
_USER_SCOPE_REF = RBACElementRef(RBACElementType.USER, _USER_SCOPE_ID)


# =============================================================================
# Test Row Models
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


@dataclass
class OpsRBACScopeCreation(ScopeCreation[OpsRBACScopeRow]):
    spec: ScopeRowCreatorSpec

    @override
    def creator(self) -> RBACEntityCreator[OpsRBACScopeRow]:
        return RBACEntityCreator(
            spec=self.spec,
            element_type=RBACElementType.PROJECT,
            scope_ref=None,  # GLOBAL: no parent scope association to write
        )

    @override
    def scope_of(self, row: OpsRBACScopeRow) -> ScopeRef:
        return ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=row.id)

    @override
    def system_roles_of(self, row: OpsRBACScopeRow) -> Collection[ScopeSystemRoleData]:
        return ()


def make_scope_creation(scope_id: UUID, name: str) -> ScopeCreation[OpsRBACScopeRow]:
    return OpsRBACScopeCreation(spec=ScopeRowCreatorSpec(scope_id=scope_id, name=name))


@dataclass
class StubMember(ScopeMember):
    member_id: UUID
    role_user: UserID | None = None

    @override
    def entity_ref(self) -> EntityRef:
        return EntityRef(entity_type=_TEST_MEMBER_ENTITY_TYPE, entity_id=self.member_id)

    @override
    def assign_role_on(self) -> UserID | None:
        return self.role_user


class RBACOpsTestRow(Base):  # type: ignore[misc]
    __tablename__ = "test_rbac_ops_entity"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True)


class RBACOpsBlockerRow(Base):  # type: ignore[misc]
    """Referencing row whose RESTRICT foreign key makes its target's delete fail."""

    __tablename__ = "test_rbac_ops_blocker"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    target_id: Mapped[int] = mapped_column(
        sa.ForeignKey("test_rbac_ops_entity.id", ondelete="RESTRICT"), nullable=False
    )


@dataclass
class RBACOpsCreatorSpec(CreatorSpec[RBACOpsTestRow]):
    name: str

    @override
    def build_row(self) -> RBACOpsTestRow:
        return RBACOpsTestRow(name=self.name)


@dataclass
class RBACOpsPurgerSpec(RBACEntityPurgerSpec[RBACOpsTestRow]):
    entity_id: str

    @override
    def row_class(self) -> type[RBACOpsTestRow]:
        return RBACOpsTestRow

    @override
    def pk_value(self) -> int:
        return int(self.entity_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def element_type(self) -> RBACElementType:
        return RBACElementType.VFOLDER

    @override
    def entity_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.VFOLDER, self.entity_id)


@dataclass(frozen=True)
class _ScopedRow:
    """A scope-bound row a test purges, or collides with, detached from its session."""

    name: str
    id: int


# =============================================================================
# Tables & Fixtures
# =============================================================================

_SCOPE_TABLES = [
    OpsRBACScopeRow,
    VirtualScopeRow,
    EntityMembershipRow,
    ScopeBindingRow,
    # create_scope provisions preset-derived roles, so it reads these even when empty.
    RolePresetRow,
    RolePermissionPresetRow,
]


@pytest.fixture
async def scope_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, _SCOPE_TABLES):  # type: ignore[arg-type]
        yield


@pytest.fixture
async def rbac_ops_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(
        database_connection,
        [RBACOpsTestRow, RBACOpsBlockerRow, AssociationScopesEntitiesRow, RoleRow, PermissionRow],
    ):
        yield


_ENTITY_MEMBER_TABLES = [
    VirtualScopeRow,
    EntityMembershipRow,
    ScopeBindingRow,
    AssociationScopesEntitiesRow,
]


@pytest.fixture
async def entity_member_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, _ENTITY_MEMBER_TABLES):  # type: ignore[arg-type]
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
    """create_scope / bulk_create_scopes materialize the VS node, self-membership, and
    self scope_binding (plus a bound-scope binding when a bound_scope is given)."""

    async def test_create_scope_adds_virtual_scope_membership_and_self_binding(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_tables: None,
        single_scope: SingleScopeContext,
    ) -> None:
        """create_scope creates the VS node, registers the scope in its own VS, and binds
        the scope to its own VS."""
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
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()

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

        assert len(binding_rows) == 1
        binding = binding_rows[0]
        assert binding.virtual_scope_id == vs.id
        assert binding.scope_type == _TEST_SCOPE_TYPE
        assert binding.scope_id == scope_id
        assert binding.permission_cap is None

    async def test_create_scope_with_bound_scope_binds_it_to_its_virtual_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_tables: None,
        single_scope: SingleScopeContext,
    ) -> None:
        """create_scope(bound_scope=...) binds that scope to the new scope's VS on top of
        the self binding, so it reaches this scope's entities in one hop."""
        scope_id = single_scope.scope_id
        bound_scope = ScopeRef(scope_type=_TEST_BOUND_SCOPE_TYPE, scope_id=uuid.uuid4())

        async with provider.write_ops() as w:
            await w.create_scope(single_scope.creation, bound_scope=bound_scope)

        async with database_connection.begin_session_read_committed() as sess:
            vs = (
                await sess.execute(
                    sa.select(VirtualScopeRow).where(VirtualScopeRow.scope_id == scope_id)
                )
            ).scalar_one()
            binding_rows = (
                (
                    await sess.execute(
                        sa.select(ScopeBindingRow).where(ScopeBindingRow.virtual_scope_id == vs.id)
                    )
                )
                .scalars()
                .all()
            )

        assert {(b.scope_type, b.scope_id) for b in binding_rows} == {
            (_TEST_SCOPE_TYPE, scope_id),  # self binding
            (_TEST_BOUND_SCOPE_TYPE, bound_scope.scope_id),  # bound-scope binding
        }

    async def test_bulk_create_scopes_adds_vs_membership_and_self_binding_per_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_tables: None,
        bulk_scopes: BulkScopeContext,
    ) -> None:
        """bulk_create_scopes creates one VS node, self-membership, and self binding per
        scope."""
        scope_ids = bulk_scopes.scope_ids

        async with provider.write_ops() as w:
            await w.bulk_create_scopes(bulk_scopes.creations)

        async with database_connection.begin_session_read_committed() as sess:
            vs_rows = (await sess.execute(sa.select(VirtualScopeRow))).scalars().all()
            membership_rows = (await sess.execute(sa.select(EntityMembershipRow))).scalars().all()
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()

        assert {vs.scope_id for vs in vs_rows} == set(scope_ids)
        vs_by_scope = {vs.scope_id: vs for vs in vs_rows}

        assert len(membership_rows) == 3
        for membership in membership_rows:
            assert membership.entity_type == _TEST_ENTITY_TYPE
            assert membership.entity_id in scope_ids
            assert membership.virtual_scope_id == vs_by_scope[membership.entity_id].id
            assert membership.permission_cap is None

        assert len(binding_rows) == 3
        for binding in binding_rows:
            assert binding.scope_type == _TEST_SCOPE_TYPE
            assert binding.scope_id in scope_ids
            assert binding.virtual_scope_id == vs_by_scope[binding.scope_id].id
            assert binding.permission_cap is None


class TestEnsureScope:
    """ensure_scope backfills the VS node, self-membership, and self binding for an
    already-created scope, without creating the real scope row."""

    async def test_ensure_scope_adds_vs_membership_and_self_binding_without_real_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_tables: None,
    ) -> None:
        """ensure_scope creates the VS node, self-membership, and self binding, and leaves
        no real scope row behind."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)

        async with database_connection.begin_session_read_committed() as sess:
            vs_rows = (await sess.execute(sa.select(VirtualScopeRow))).scalars().all()
            membership_rows = (await sess.execute(sa.select(EntityMembershipRow))).scalars().all()
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            real_row_count = await sess.scalar(
                sa.select(sa.func.count()).select_from(OpsRBACScopeRow)
            )

        assert len(vs_rows) == 1
        vs = vs_rows[0]
        assert vs.scope_id == scope_id

        assert len(membership_rows) == 1
        assert membership_rows[0].virtual_scope_id == vs.id
        assert membership_rows[0].entity_id == scope_id

        assert len(binding_rows) == 1
        assert binding_rows[0].virtual_scope_id == vs.id
        assert binding_rows[0].scope_id == scope_id
        assert binding_rows[0].permission_cap is None

        assert real_row_count == 0

    async def test_ensure_scope_is_idempotent(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_tables: None,
    ) -> None:
        """Calling ensure_scope twice leaves exactly one VS node, membership, and binding."""
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(scope)

        async with database_connection.begin_session_read_committed() as sess:
            vs_count = await sess.scalar(sa.select(sa.func.count()).select_from(VirtualScopeRow))
            membership_count = await sess.scalar(
                sa.select(sa.func.count()).select_from(EntityMembershipRow)
            )
            binding_count = await sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeBindingRow)
            )

        assert vs_count == 1
        assert membership_count == 1
        assert binding_count == 1

    async def test_ensure_scope_with_bound_scope_adds_binding(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_tables: None,
    ) -> None:
        """ensure_scope(scope, bound_scope) binds both the scope itself and the bound scope
        to the scope's VS."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        bound_scope = ScopeRef(scope_type=_TEST_BOUND_SCOPE_TYPE, scope_id=uuid.uuid4())

        async with provider.write_ops() as w:
            await w.ensure_scope(scope, bound_scope=bound_scope)

        async with database_connection.begin_session_read_committed() as sess:
            vs = (
                await sess.execute(
                    sa.select(VirtualScopeRow).where(VirtualScopeRow.scope_id == scope_id)
                )
            ).scalar_one()
            binding_rows = (
                (
                    await sess.execute(
                        sa.select(ScopeBindingRow).where(ScopeBindingRow.virtual_scope_id == vs.id)
                    )
                )
                .scalars()
                .all()
            )

        assert {(b.scope_type, b.scope_id) for b in binding_rows} == {
            (_TEST_SCOPE_TYPE, scope_id),  # self binding
            (_TEST_BOUND_SCOPE_TYPE, bound_scope.scope_id),  # bound-scope binding
        }


@pytest.fixture
async def scoped_rows(
    database_connection: ExtendedAsyncSAEngine,
    rbac_ops_tables: None,
) -> list[_ScopedRow]:
    """Two committed rows bound to ``_USER_SCOPE_REF``, each with its scope association.

    Inserted directly rather than through the scoped ops, so a broken op under test fails
    the assertion instead of the arrange step.
    """
    async with database_connection.begin_session() as db_sess:
        rows = [RBACOpsTestRow(name=name) for name in ("first", "second")]
        db_sess.add_all(rows)
        await db_sess.flush()
        db_sess.add_all([
            AssociationScopesEntitiesRow(
                scope_type=_USER_SCOPE_REF.element_type.to_scope_type(),
                scope_id=_USER_SCOPE_ID,
                entity_type=EntityType.VFOLDER,
                entity_id=str(row.id),
                relation_type=RelationType.AUTO,
            )
            for row in rows
        ])
        return [_ScopedRow(name=row.name, id=row.id) for row in rows]


@pytest.fixture
async def blocking_reference(
    database_connection: ExtendedAsyncSAEngine,
    scoped_rows: list[_ScopedRow],
) -> None:
    """A RESTRICT reference onto the first scoped row, making its delete fail."""
    async with database_connection.begin_session() as db_sess:
        db_sess.add(RBACOpsBlockerRow(target_id=scoped_rows[0].id))


@dataclass(frozen=True)
class _ScopedCreateCase:
    """A creator to run through a scoped create, and the associations it should leave."""

    name: str
    scope_ref: RBACElementRef | None
    expected_scope_ids: list[str] = field(default_factory=list)


class TestBulkCreateScopedPartial:
    @pytest.mark.parametrize(
        "case",
        [
            _ScopedCreateCase(
                name="scoped",
                scope_ref=_USER_SCOPE_REF,
                expected_scope_ids=[_USER_SCOPE_ID],
            ),
            _ScopedCreateCase(name="global", scope_ref=None),
        ],
        ids=lambda case: case.name,
    )
    async def test_row_binds_to_the_scope_its_creator_carries(
        self,
        case: _ScopedCreateCase,
        provider: RBACOpsProvider,
        database_connection: ExtendedAsyncSAEngine,
        rbac_ops_tables: None,
    ) -> None:
        """A scoped creator binds its row to its scope; a scope-less one associates nothing."""
        async with provider.write_ops() as w:
            result = await w.bulk_create_scoped_partial([
                RBACEntityCreator(
                    spec=RBACOpsCreatorSpec(name=case.name),
                    element_type=RBACElementType.VFOLDER,
                    scope_ref=case.scope_ref,
                )
            ])
            assert [row.name for row in result.successes] == [case.name]
            assert result.errors == []
            entity_id = str(result.successes[0].id)

        async with database_connection.begin_readonly_session() as db_sess:
            scope_ids = await db_sess.scalars(
                sa.select(AssociationScopesEntitiesRow.scope_id).where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.VFOLDER,
                    AssociationScopesEntitiesRow.entity_id == entity_id,
                )
            )
            assert list(scope_ids) == case.expected_scope_ids

    async def test_rejected_item_leaves_the_rest_created(
        self,
        provider: RBACOpsProvider,
        database_connection: ExtendedAsyncSAEngine,
        scoped_rows: list[_ScopedRow],
    ) -> None:
        """A row and its association share one savepoint, so a rejected row rolls back both."""
        async with provider.write_ops() as w:
            result = await w.bulk_create_scoped_partial([
                RBACEntityCreator(  # unique violation on `name` -> rejected
                    spec=RBACOpsCreatorSpec(name=scoped_rows[0].name),
                    element_type=RBACElementType.VFOLDER,
                    scope_ref=_USER_SCOPE_REF,
                ),
                RBACEntityCreator(
                    spec=RBACOpsCreatorSpec(name="fresh"),
                    element_type=RBACElementType.VFOLDER,
                    scope_ref=_USER_SCOPE_REF,
                ),
            ])
            assert [row.name for row in result.successes] == ["fresh"]
            assert [e.index for e in result.errors] == [0]
            fresh_id = str(result.successes[0].id)

        async with database_connection.begin_readonly_session() as db_sess:
            names = await db_sess.scalars(sa.select(RBACOpsTestRow.name))
            assert sorted(names) == ["first", "fresh", "second"]
            # the surviving row kept its association, and the rejected one left none behind
            fresh_scope_ids = await db_sess.scalars(
                sa.select(AssociationScopesEntitiesRow.scope_id).where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.VFOLDER,
                    AssociationScopesEntitiesRow.entity_id == fresh_id,
                )
            )
            assert list(fresh_scope_ids) == [_USER_SCOPE_ID]
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 3  # one per surviving row, none orphaned by the rejection


class TestBulkPurgeScopedPartial:
    async def test_purges_rows_and_their_associations(
        self,
        provider: RBACOpsProvider,
        database_connection: ExtendedAsyncSAEngine,
        scoped_rows: list[_ScopedRow],
    ) -> None:
        """Deleting a row takes its scope association with it, leaving nothing orphaned."""
        doomed, kept = scoped_rows
        async with provider.write_ops() as w:
            result = await w.bulk_purge_scoped_partial([
                RBACEntityPurger(
                    spec=RBACOpsPurgerSpec(entity_id=str(doomed.id)),
                )
            ])
            assert [row.name for row in result.successes] == [doomed.name]
            assert result.errors == []

        async with database_connection.begin_readonly_session() as db_sess:
            names = await db_sess.scalars(sa.select(RBACOpsTestRow.name))
            assert list(names) == [kept.name]
            doomed_scope_ids = await db_sess.scalars(
                sa.select(AssociationScopesEntitiesRow.scope_id).where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.VFOLDER,
                    AssociationScopesEntitiesRow.entity_id == str(doomed.id),
                )
            )
            assert list(doomed_scope_ids) == []

    async def test_missing_row_is_skipped_not_reported(
        self,
        provider: RBACOpsProvider,
        database_connection: ExtendedAsyncSAEngine,
        scoped_rows: list[_ScopedRow],
    ) -> None:
        """A purger for an already-gone row yields no success and no error, like the unscoped op."""
        async with provider.write_ops() as w:
            result = await w.bulk_purge_scoped_partial([
                RBACEntityPurger(
                    spec=RBACOpsPurgerSpec(entity_id="9999999"),
                )
            ])
            assert result.successes == []
            assert result.errors == []

        # the untouched rows and their associations are still there
        async with database_connection.begin_readonly_session() as db_sess:
            names = await db_sess.scalars(sa.select(RBACOpsTestRow.name))
            assert sorted(names) == [row.name for row in scoped_rows]
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == len(scoped_rows)

    async def test_failed_row_leaves_the_rest_purged(
        self,
        provider: RBACOpsProvider,
        database_connection: ExtendedAsyncSAEngine,
        scoped_rows: list[_ScopedRow],
        blocking_reference: None,
    ) -> None:
        """A row whose delete violates a constraint fails alone: its RBAC cleanup rolls back
        with it, and the batch carries on rather than dying on the aborted savepoint."""
        blocked, free = scoped_rows
        async with provider.write_ops() as w:
            result = await w.bulk_purge_scoped_partial([
                RBACEntityPurger(  # RESTRICT foreign key -> delete rejected
                    spec=RBACOpsPurgerSpec(entity_id=str(blocked.id)),
                ),
                RBACEntityPurger(
                    spec=RBACOpsPurgerSpec(entity_id=str(free.id)),
                ),
            ])
            assert [row.name for row in result.successes] == [free.name]
            assert [e.index for e in result.errors] == [0]

        async with database_connection.begin_readonly_session() as db_sess:
            names = await db_sess.scalars(sa.select(RBACOpsTestRow.name))
            assert list(names) == [blocked.name]
            # the failed row kept the association its rolled-back cleanup had deleted
            blocked_scope_ids = await db_sess.scalars(
                sa.select(AssociationScopesEntitiesRow.scope_id).where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.VFOLDER,
                    AssociationScopesEntitiesRow.entity_id == str(blocked.id),
                )
            )
            assert list(blocked_scope_ids) == [_USER_SCOPE_ID]


class TestAddEntityMembers:
    """add_entity_members writes both the virtual-scope membership and the scope association."""

    async def test_add_entity_members_writes_membership_and_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """Each member gets a VS membership row and a scope association row."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        member_ids = [uuid.uuid4(), uuid.uuid4()]

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.add_entity_members(
                EntityMembersAddition(
                    scope=scope,
                    members=[StubMember(member_id=mid) for mid in member_ids],
                )
            )

        async with database_connection.begin_session_read_committed() as sess:
            vs = (
                await sess.execute(
                    sa.select(VirtualScopeRow).where(VirtualScopeRow.scope_id == scope_id)
                )
            ).scalar_one()
            membership_ids = set(
                (
                    await sess.scalars(
                        sa.select(EntityMembershipRow.entity_id).where(
                            EntityMembershipRow.virtual_scope_id == vs.id,
                            EntityMembershipRow.entity_type == _TEST_MEMBER_ENTITY_TYPE,
                        )
                    )
                ).all()
            )
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

    async def test_add_entity_members_is_idempotent(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """Re-adding the same member is a no-op — no duplicate membership or association."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        member_id = uuid.uuid4()
        addition = EntityMembersAddition(scope=scope, members=[StubMember(member_id=member_id)])

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.add_entity_members(addition)
            await w.add_entity_members(addition)

        async with database_connection.begin_session_read_committed() as sess:
            membership_count = await sess.scalar(
                sa.select(sa.func.count())
                .select_from(EntityMembershipRow)
                .where(EntityMembershipRow.entity_type == _TEST_MEMBER_ENTITY_TYPE)
            )
            assoc_count = await sess.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(AssociationScopesEntitiesRow.entity_id == str(member_id))
            )

        assert membership_count == 1
        assert assoc_count == 1


class TestRemoveEntityMembers:
    """remove_entity_members deletes both the VS membership and the scope association."""

    async def test_remove_entity_members_deletes_membership_and_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """The removed member loses both rows; the other member keeps both."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        removed_id, kept_id = uuid.uuid4(), uuid.uuid4()

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.add_entity_members(
                EntityMembersAddition(
                    scope=scope,
                    members=[StubMember(member_id=removed_id), StubMember(member_id=kept_id)],
                )
            )
            await w.remove_entity_members(
                scope,
                [EntityRef(entity_type=_TEST_MEMBER_ENTITY_TYPE, entity_id=removed_id)],
            )

        async with database_connection.begin_session_read_committed() as sess:
            membership_ids = set(
                (
                    await sess.scalars(
                        sa.select(EntityMembershipRow.entity_id).where(
                            EntityMembershipRow.entity_type == _TEST_MEMBER_ENTITY_TYPE,
                        )
                    )
                ).all()
            )
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
