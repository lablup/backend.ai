"""Integration tests for the RBAC ops provider (RBACWriteOps) with a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Collection, Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

import aiohttp.web
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_SCOPE_TYPE
from ai.backend.common.data.entity.types import (
    EntityRef,
    ScopeRef,
    ScopeType,
)
from ai.backend.common.data.entity.types import (
    EntityType as VirtualScopeEntityType,
)
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.common.data.permission.types import (
    EntityType,
    Permission,
    RBACElementType,
    RelationType,
)
from ai.backend.common.data.permission.types import ScopeType as PermissionScopeType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.permission import VirtualScopeNotFound
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UnsupportedCompositePrimaryKeyError,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
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
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow, ScalingGroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.base import CreatorSpec, IntegrityErrorCheck
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.rbac.entity_purger import (
    RBACEntityBatchPurger,
    RBACEntityBatchPurgerSpec,
    RBACEntityPurger,
    RBACEntityPurgerSpec,
)
from ai.backend.manager.repositories.base.rbac.entity_upserter import (
    ConflictTarget,
    RBACEntityUpserter,
)
from ai.backend.manager.repositories.base.types import ConflictCheck
from ai.backend.manager.repositories.base.upserter import UpserterSpec
from ai.backend.manager.repositories.ops.rbac.provider import (
    EntityMembersAddition,
    RBACOpsProvider,
    ScopeBatchDeletion,
    ScopeCreation,
    ScopeDeletion,
    ScopeEntityMember,
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

# A scope that carries roles must name a type the permission layer knows.
_TEST_SCOPE_TYPE = ScopeType(PermissionScopeType.PROJECT.value)
_TEST_ENTITY_TYPE = VirtualScopeEntityType(PermissionScopeType.PROJECT.value)
_TEST_MEMBER_ENTITY_TYPE = VirtualScopeEntityType(RBACElementType.USER.value)
_TEST_MEMBER_SCOPE_TYPE = ScopeType(RBACElementType.USER.value)

_USER_SCOPE_ID = str(uuid.uuid4())
_USER_SCOPE_REF = RBACElementRef(RBACElementType.USER, _USER_SCOPE_ID)
_PROJECT_SCOPE_ID = str(uuid.uuid4())
_PROJECT_SCOPE_REF = RBACElementRef(RBACElementType.PROJECT, _PROJECT_SCOPE_ID)
_UPSERT_ENTITY_NAME = "fragment"
_UPSERT_EXISTING_ROW_ID = UUID("11111111-1111-1111-1111-111111111111")


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
    entity_type: VirtualScopeEntityType = _TEST_MEMBER_ENTITY_TYPE

    @override
    def entity_ref(self) -> EntityRef:
        return EntityRef(entity_type=self.entity_type, entity_id=self.member_id)

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
    self scope_binding."""

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


class TestAddBulkMembers:
    """add_bulk_members enrolls each member into the scope's VS (with its scope
    association) and binds the scope into the member's own VS — never the reverse
    binding."""

    async def test_writes_membership_association_and_binding(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """Each member gets membership, association, and the scope's binding (with cap)
        in its own VS — and no reverse binding in the scope's VS."""
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
                    members=[StubMember(member_id=mid) for mid in member_ids],
                ),
                permission_cap=Permission.READ,
            )

        async with database_connection.begin_session_read_committed() as sess:
            vs_rows = (await sess.execute(sa.select(VirtualScopeRow))).scalars().all()
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            vs_by_scope = {vs.scope_id: vs.id for vs in vs_rows}
            membership_ids = set(
                (
                    await sess.scalars(
                        sa.select(EntityMembershipRow.entity_id).where(
                            EntityMembershipRow.virtual_scope_id == vs_by_scope[scope_id],
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

        for mid in member_ids:
            member_bindings = {
                (b.scope_type, b.scope_id): b.permission_cap
                for b in binding_rows
                if b.virtual_scope_id == vs_by_scope[mid]
            }
            assert member_bindings == {
                (_TEST_MEMBER_SCOPE_TYPE, mid): None,  # self binding
                (_TEST_SCOPE_TYPE, scope_id): Permission.READ,
            }
        scope_vs_bindings = {
            (b.scope_type, b.scope_id)
            for b in binding_rows
            if b.virtual_scope_id == vs_by_scope[scope_id]
        }
        assert scope_vs_bindings == {(_TEST_SCOPE_TYPE, scope_id)}  # self binding only

    async def test_readd_is_idempotent_and_keeps_binding_cap(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """Re-adding the same member with a different cap is a no-op — no duplicate
        membership or association, and the original binding cap is kept."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        member_id = uuid.uuid4()
        member_scope = ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=member_id)
        addition = EntityMembersAddition(scope=scope, members=[StubMember(member_id=member_id)])

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(member_scope)
            await w.add_bulk_members(addition, permission_cap=Permission.READ)
            await w.add_bulk_members(addition, permission_cap=Permission.full())

        async with database_connection.begin_session_read_committed() as sess:
            scope_vs = (
                await sess.execute(
                    sa.select(VirtualScopeRow).where(VirtualScopeRow.scope_id == scope_id)
                )
            ).scalar_one()
            member_vs = (
                await sess.execute(
                    sa.select(VirtualScopeRow).where(VirtualScopeRow.scope_id == member_id)
                )
            ).scalar_one()
            membership_count = await sess.scalar(
                sa.select(sa.func.count())
                .select_from(EntityMembershipRow)
                .where(EntityMembershipRow.virtual_scope_id == scope_vs.id)
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
                            ScopeBindingRow.virtual_scope_id == member_vs.id
                        )
                    )
                )
                .scalars()
                .all()
            )

        # the scope's self membership and the member's
        assert membership_count == 2
        assert assoc_count == 1
        caps_by_scope = {(b.scope_type, b.scope_id): b.permission_cap for b in binding_rows}
        assert caps_by_scope == {
            (_TEST_MEMBER_SCOPE_TYPE, member_id): None,  # self binding
            (_TEST_SCOPE_TYPE, scope_id): Permission.READ,
        }

    async def test_missing_member_vs_fails_the_whole_call(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """One member without a VS raises VirtualScopeNotFound and nothing is written —
        no membership and no binding, not even for the members whose VS exists."""
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())
        present_id, missing_id = uuid.uuid4(), uuid.uuid4()

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=present_id))

        with pytest.raises(VirtualScopeNotFound):
            async with provider.write_ops() as w:
                await w.add_bulk_members(
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

        assert {(b.scope_type, b.scope_id) for b in binding_rows} == {
            (_TEST_SCOPE_TYPE, scope.scope_id),  # self bindings only
            (_TEST_MEMBER_SCOPE_TYPE, present_id),
        }
        assert {(m.entity_type, m.entity_id) for m in membership_rows} == {
            (_TEST_ENTITY_TYPE, scope.scope_id),  # self memberships only
            (_TEST_MEMBER_ENTITY_TYPE, present_id),
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


class TestRemoveBulkMembers:
    """remove_bulk_members deletes the VS membership, the scope association, and the
    scope's binding in the member's own VS — and never raises for missing virtual
    scopes."""

    async def test_remove_deletes_membership_association_and_binding(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """The removed member loses all three rows — its own VS keeps only the self
        binding — while the other member keeps all of them."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        removed_id, kept_id = uuid.uuid4(), uuid.uuid4()

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            for mid in (removed_id, kept_id):
                await w.ensure_scope(ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=mid))
            await w.add_bulk_members(
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
            vs_rows = (await sess.execute(sa.select(VirtualScopeRow))).scalars().all()
            vs_by_scope = {vs.scope_id: vs.id for vs in vs_rows}
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            membership_ids = set(
                (
                    await sess.scalars(
                        sa.select(EntityMembershipRow.entity_id).where(
                            EntityMembershipRow.virtual_scope_id == vs_by_scope[scope_id],
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
        removed_bindings = {
            (b.scope_type, b.scope_id)
            for b in binding_rows
            if b.virtual_scope_id == vs_by_scope[removed_id]
        }
        assert removed_bindings == {(_TEST_MEMBER_SCOPE_TYPE, removed_id)}  # self binding only
        kept_bindings = {
            (b.scope_type, b.scope_id)
            for b in binding_rows
            if b.virtual_scope_id == vs_by_scope[kept_id]
        }
        assert kept_bindings == {
            (_TEST_MEMBER_SCOPE_TYPE, kept_id),
            (_TEST_SCOPE_TYPE, scope_id),
        }

    async def test_remove_without_member_vs_still_deletes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """A member without a VS (legacy data) still loses its membership and
        association — the removal does not raise."""
        scope_id = uuid.uuid4()
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        member_id = uuid.uuid4()

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)

        async with database_connection.begin_session() as sess:
            scope_vs = (
                await sess.execute(
                    sa.select(VirtualScopeRow).where(VirtualScopeRow.scope_id == scope_id)
                )
            ).scalar_one()
            sess.add(
                EntityMembershipRow(
                    virtual_scope_id=scope_vs.id,
                    entity_type=_TEST_MEMBER_ENTITY_TYPE,
                    entity_id=member_id,
                    permission_cap=None,
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
                .where(EntityMembershipRow.entity_id == member_id)
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
            entity_type=VirtualScopeEntityType("unregistered-type"),
        )

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(
                ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=valid.member_id)
            )
            await w.ensure_scope(
                ScopeRef(scope_type=ScopeType("unregistered-type"), scope_id=invalid.member_id)
            )
            result = await w.add_bulk_members_partial(
                EntityMembersAddition(scope=scope, members=[valid, invalid])
            )

        assert result.successes == [valid]
        assert [error.member for error in result.errors] == [invalid]
        assert result.errors[0].index == 1

        async with database_connection.begin_session_read_committed() as sess:
            scope_vs = (
                await sess.execute(
                    sa.select(VirtualScopeRow).where(VirtualScopeRow.scope_id == scope.scope_id)
                )
            ).scalar_one()
            membership_rows = (
                (
                    await sess.execute(
                        sa.select(EntityMembershipRow).where(
                            EntityMembershipRow.virtual_scope_id == scope_vs.id
                        )
                    )
                )
                .scalars()
                .all()
            )
            assoc_ids = set(
                (
                    await sess.scalars(
                        sa.select(AssociationScopesEntitiesRow.entity_id).where(
                            AssociationScopesEntitiesRow.scope_id == str(scope.scope_id)
                        )
                    )
                ).all()
            )

        assert {(m.entity_type, m.entity_id) for m in membership_rows} == {
            (_TEST_ENTITY_TYPE, scope.scope_id),  # self membership
            (_TEST_MEMBER_ENTITY_TYPE, valid.member_id),
        }
        assert assoc_ids == {str(valid.member_id)}

    async def test_missing_member_vs_is_isolated(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        entity_member_tables: None,
    ) -> None:
        """The member without a VS lands in errors with nothing written for it; the
        valid member gets its membership, association, and binding."""
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())
        valid = StubMember(member_id=uuid.uuid4())
        missing = StubMember(member_id=uuid.uuid4())

        async with provider.write_ops() as w:
            await w.ensure_scope(scope)
            await w.ensure_scope(
                ScopeRef(scope_type=_TEST_MEMBER_SCOPE_TYPE, scope_id=valid.member_id)
            )
            result = await w.add_bulk_members_partial(
                EntityMembersAddition(scope=scope, members=[valid, missing]),
                permission_cap=Permission.READ,
            )

        assert result.successes == [valid]
        assert [error.member for error in result.errors] == [missing]
        assert isinstance(result.errors[0].exception, VirtualScopeNotFound)

        async with database_connection.begin_session_read_committed() as sess:
            vs_rows = (await sess.execute(sa.select(VirtualScopeRow))).scalars().all()
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            vs_by_scope = {vs.scope_id: vs.id for vs in vs_rows}
            membership_ids = set(
                (
                    await sess.scalars(
                        sa.select(EntityMembershipRow.entity_id).where(
                            EntityMembershipRow.virtual_scope_id == vs_by_scope[scope.scope_id],
                            EntityMembershipRow.entity_type == _TEST_MEMBER_ENTITY_TYPE,
                        )
                    )
                ).all()
            )

        assert missing.member_id not in vs_by_scope
        assert membership_ids == {valid.member_id}
        valid_bindings = {
            (b.scope_type, b.scope_id): b.permission_cap
            for b in binding_rows
            if b.virtual_scope_id == vs_by_scope[valid.member_id]
        }
        assert valid_bindings == {
            (_TEST_MEMBER_SCOPE_TYPE, valid.member_id): None,  # self binding
            (_TEST_SCOPE_TYPE, scope.scope_id): Permission.READ,
        }


# =============================================================================
# Scope deletion: virtual-scope edge cleanup
# =============================================================================


@dataclass
class ScopeRowPurgerSpec(RBACEntityPurgerSpec[OpsRBACScopeRow]):
    scope_id: UUID

    @override
    def row_class(self) -> type[OpsRBACScopeRow]:
        return OpsRBACScopeRow

    @override
    def pk_value(self) -> UUID:
        return self.scope_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def element_type(self) -> RBACElementType:
        return RBACElementType.PROJECT

    @override
    def entity_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.scope_id))


@dataclass
class ScopeRowBatchPurgerSpec(RBACEntityBatchPurgerSpec[OpsRBACScopeRow]):
    scope_ids: Sequence[UUID]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[OpsRBACScopeRow]]:
        return sa.select(OpsRBACScopeRow).where(OpsRBACScopeRow.id.in_(self.scope_ids))

    @override
    def element_type(self) -> RBACElementType:
        return RBACElementType.PROJECT

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


_SCOPE_DELETE_TABLES = [
    OpsRBACScopeRow,
    VirtualScopeRow,
    EntityMembershipRow,
    ScopeBindingRow,
    RolePresetRow,
    RolePermissionPresetRow,
    AssociationScopesEntitiesRow,
    PermissionRow,
]


@pytest.fixture
async def scope_delete_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, _SCOPE_DELETE_TABLES):  # type: ignore[arg-type]
        yield


class TestScopeDeletionVirtualScopeCleanup:
    """delete_scope / batch_delete_scopes remove not only the scope's own VS node but
    also the edges the scope left in other virtual scopes: its bindings as the reaching
    side and its entity memberships."""

    async def test_delete_scope_removes_edges_in_other_virtual_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_delete_tables: None,
        single_scope: SingleScopeContext,
    ) -> None:
        """The deleted scope's binding and membership in another VS are removed; the
        other VS keeps its node and self edges."""
        scope_id = single_scope.scope_id
        scope = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=scope_id)
        other = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())

        async with provider.write_ops() as w:
            await w.create_scope(single_scope.creation)
            await w.ensure_scope(other)
            # Two-way membership leaves scope's binding and membership in other's VS.
            await w.add_bulk_members(
                EntityMembersAddition(
                    scope=scope,
                    members=[
                        ScopeEntityMember(
                            ref=EntityRef(entity_type=_TEST_ENTITY_TYPE, entity_id=other.scope_id)
                        )
                    ],
                )
            )
            await w.add_bulk_members(
                EntityMembersAddition(
                    scope=other,
                    members=[
                        ScopeEntityMember(
                            ref=EntityRef(entity_type=_TEST_ENTITY_TYPE, entity_id=scope_id)
                        )
                    ],
                )
            )

        async with provider.write_ops() as w:
            result = await w.delete_scope(
                ScopeDeletion(
                    purger=RBACEntityPurger(spec=ScopeRowPurgerSpec(scope_id=scope_id)),
                    scope=scope,
                )
            )

        assert result is not None

        async with database_connection.begin_session_read_committed() as sess:
            vs_rows = (await sess.execute(sa.select(VirtualScopeRow))).scalars().all()
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            membership_rows = (await sess.execute(sa.select(EntityMembershipRow))).scalars().all()

        assert {vs.scope_id for vs in vs_rows} == {other.scope_id}
        assert {(b.scope_type, b.scope_id) for b in binding_rows} == {
            (_TEST_SCOPE_TYPE, other.scope_id),  # the other VS keeps only its self binding
        }
        assert {(m.entity_type, m.entity_id) for m in membership_rows} == {
            (_TEST_ENTITY_TYPE, other.scope_id),  # and only its self membership
        }

    async def test_batch_delete_scopes_removes_edges_in_other_virtual_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        scope_delete_tables: None,
        bulk_scopes: BulkScopeContext,
    ) -> None:
        """Every batch-deleted scope's binding and membership in the surviving VS are
        removed along with the real rows."""
        scope_ids = bulk_scopes.scope_ids
        scopes = [ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=sid) for sid in scope_ids]
        other = ScopeRef(scope_type=_TEST_SCOPE_TYPE, scope_id=uuid.uuid4())

        async with provider.write_ops() as w:
            await w.bulk_create_scopes(bulk_scopes.creations)
            await w.ensure_scope(other)
            # Two-way membership leaves each scope's binding and membership in other's VS.
            for scope in scopes:
                await w.add_bulk_members(
                    EntityMembersAddition(
                        scope=scope,
                        members=[
                            ScopeEntityMember(
                                ref=EntityRef(
                                    entity_type=_TEST_ENTITY_TYPE, entity_id=other.scope_id
                                )
                            )
                        ],
                    )
                )
            await w.add_bulk_members(
                EntityMembersAddition(
                    scope=other,
                    members=[
                        ScopeEntityMember(
                            ref=EntityRef(entity_type=_TEST_ENTITY_TYPE, entity_id=sid)
                        )
                        for sid in scope_ids
                    ],
                )
            )

        async with provider.write_ops() as w:
            result = await w.batch_delete_scopes(
                ScopeBatchDeletion(
                    purger=RBACEntityBatchPurger(spec=ScopeRowBatchPurgerSpec(scope_ids=scope_ids)),
                    scopes=scopes,
                )
            )

        assert result.deleted_count == len(scope_ids)

        async with database_connection.begin_session_read_committed() as sess:
            real_row_count = await sess.scalar(
                sa.select(sa.func.count()).select_from(OpsRBACScopeRow)
            )
            vs_rows = (await sess.execute(sa.select(VirtualScopeRow))).scalars().all()
            binding_rows = (await sess.execute(sa.select(ScopeBindingRow))).scalars().all()
            membership_rows = (await sess.execute(sa.select(EntityMembershipRow))).scalars().all()

        assert real_row_count == 0
        assert {vs.scope_id for vs in vs_rows} == {other.scope_id}
        assert {(b.scope_type, b.scope_id) for b in binding_rows} == {
            (_TEST_SCOPE_TYPE, other.scope_id),
        }
        assert {(m.entity_type, m.entity_id) for m in membership_rows} == {
            (_TEST_ENTITY_TYPE, other.scope_id),
        }


# =============================================================================
# upsert_scoped
# =============================================================================


class RBACOpsUpsertRow(Base):  # type: ignore[misc]
    """Upsert target: one row per (name, scope_type, scope_id), public rows keyed by name."""

    __tablename__ = "test_rbac_ops_upsert"
    __table_args__ = (
        sa.UniqueConstraint("name", "scope_type", "scope_id", name="uq_test_rbac_ops_upsert"),
        # NULLs are distinct to a unique constraint, so public rows need their own index.
        sa.Index(
            "uq_test_rbac_ops_upsert_public",
            "name",
            "scope_type",
            unique=True,
            postgresql_where=sa.text("scope_id IS NULL"),
        ),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    scope_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    scope_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    value: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class RBACOpsUpsertGatedRow(Base):  # type: ignore[misc]
    """Upsert target whose self-referencing FK gates the insert."""

    __tablename__ = "test_rbac_ops_upsert_gated"
    __table_args__ = (
        sa.UniqueConstraint("name", name="uq_test_rbac_ops_upsert_gated_name"),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        GUID, sa.ForeignKey("test_rbac_ops_upsert_gated.id"), nullable=True
    )


class RBACOpsUpsertCompositePKRow(Base):  # type: ignore[misc]
    """Upsert target with a composite primary key, which the write op rejects."""

    __tablename__ = "test_rbac_ops_upsert_composite_pk"
    __table_args__ = {"extend_existing": True}

    tenant_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    value: Mapped[str] = mapped_column(sa.String(64), nullable=False)


@dataclass
class RBACOpsUpserterSpec(UpserterSpec[RBACOpsUpsertRow]):
    """Upserts one scoped row, updating only its value on conflict."""

    scope_type: str
    scope_id: str | None
    value: str

    @property
    @override
    def row_class(self) -> type[RBACOpsUpsertRow]:
        return RBACOpsUpsertRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "name": _UPSERT_ENTITY_NAME,
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "value": self.value,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"value": self.value}


class _TestUpsertParentMissingError(BackendAIError, aiohttp.web.HTTPBadRequest):
    """Test domain error the FK gate violation maps to."""

    error_type = "https://api.backend.ai/probs/test-rbac-ops-upsert-parent-missing"
    error_title = "Parent does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


@dataclass
class RBACOpsGatedUpserterSpec(UpserterSpec[RBACOpsUpsertGatedRow]):
    """Upserts a row behind a FK gate, mapping the violation to a domain error."""

    parent_id: UUID | None
    name: str

    @property
    @override
    def row_class(self) -> type[RBACOpsUpsertGatedRow]:
        return RBACOpsUpsertGatedRow

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=_TestUpsertParentMissingError(extra_msg="parent does not exist"),
            ),
        )

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"name": self.name, "parent_id": self.parent_id}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"parent_id": self.parent_id}


@dataclass
class RBACOpsCompositePKUpserterSpec(UpserterSpec[RBACOpsUpsertCompositePKRow]):
    @property
    @override
    def row_class(self) -> type[RBACOpsUpsertCompositePKRow]:
        return RBACOpsUpsertCompositePKRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"tenant_id": 1, "item_id": 1, "value": "after"}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"value": "after"}


@dataclass(frozen=True)
class _UpsertBinding:
    """A scope association the upsert is expected to leave behind."""

    scope_type: PermissionScopeType
    scope_id: str


@dataclass(frozen=True)
class _UpsertCase:
    name: str
    scope_type: str
    scope_id: str | None
    scope_ref: RBACElementRef | None
    conflict_target: ConflictTarget
    additional_scope_refs: list[RBACElementRef]
    expected_bindings: list[_UpsertBinding]


_UPSERT_TABLES = [RBACOpsUpsertRow, AssociationScopesEntitiesRow]
_UPSERT_GATED_TABLES = [RBACOpsUpsertGatedRow, AssociationScopesEntitiesRow]


@pytest.fixture
async def upsert_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, _UPSERT_TABLES):  # type: ignore[arg-type]
        yield


@pytest.fixture
async def upsert_gated_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, _UPSERT_GATED_TABLES):  # type: ignore[arg-type]
        yield


@pytest.fixture
async def upsert_composite_pk_table(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with database_connection.begin() as conn:
        await conn.run_sync(
            lambda c: RBACOpsUpsertCompositePKRow.__table__.create(c, checkfirst=True)
        )
    yield
    async with database_connection.begin() as conn:
        await conn.run_sync(
            lambda c: RBACOpsUpsertCompositePKRow.__table__.drop(c, checkfirst=True)
        )


@pytest.fixture
async def seeded_upsert_case(
    database_connection: ExtendedAsyncSAEngine,
    upsert_tables: None,
    request: pytest.FixtureRequest,
) -> _UpsertCase:
    """Insert the conflicting row and its bindings directly, bypassing the write op."""
    case: _UpsertCase = request.param
    async with database_connection.begin_session() as db_sess:
        await db_sess.execute(
            sa.insert(RBACOpsUpsertRow).values(
                id=_UPSERT_EXISTING_ROW_ID,
                name=_UPSERT_ENTITY_NAME,
                scope_type=case.scope_type,
                scope_id=case.scope_id,
                value="before",
            )
        )
        for binding in case.expected_bindings:
            await db_sess.execute(
                sa.insert(AssociationScopesEntitiesRow).values(
                    scope_type=binding.scope_type,
                    scope_id=binding.scope_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(_UPSERT_EXISTING_ROW_ID),
                )
            )
    return case


class TestUpsertScoped:
    """A scoped upsert inserts and binds, or updates in place and keeps the binding it has."""

    @pytest.mark.parametrize(
        "case",
        [
            _UpsertCase(
                name="user-scope",
                scope_type="user",
                scope_id=_USER_SCOPE_ID,
                scope_ref=_USER_SCOPE_REF,
                conflict_target=ConflictTarget(columns=["name", "scope_type", "scope_id"]),
                additional_scope_refs=[],
                expected_bindings=[_UpsertBinding(PermissionScopeType.USER, _USER_SCOPE_ID)],
            ),
            _UpsertCase(
                name="project-scope-with-additional-user",
                scope_type="project",
                scope_id=_PROJECT_SCOPE_ID,
                scope_ref=_PROJECT_SCOPE_REF,
                conflict_target=ConflictTarget(columns=["name", "scope_type", "scope_id"]),
                additional_scope_refs=[_USER_SCOPE_REF],
                expected_bindings=[
                    _UpsertBinding(PermissionScopeType.PROJECT, _PROJECT_SCOPE_ID),
                    _UpsertBinding(PermissionScopeType.USER, _USER_SCOPE_ID),
                ],
            ),
            _UpsertCase(
                name="public-partial-index",
                scope_type="public",
                scope_id=None,
                scope_ref=None,
                conflict_target=ConflictTarget(
                    columns=["name", "scope_type"],
                    index_predicate=RBACOpsUpsertRow.scope_id.is_(None),
                ),
                additional_scope_refs=[],
                expected_bindings=[],
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_insert_binds_new_row(
        self,
        provider: RBACOpsProvider,
        database_connection: ExtendedAsyncSAEngine,
        upsert_tables: None,
        case: _UpsertCase,
    ) -> None:
        """An inserted row binds to every scope its upserter carries."""
        async with provider.write_ops() as w:
            result = await w.upsert_scoped(
                RBACEntityUpserter(
                    spec=RBACOpsUpserterSpec(case.scope_type, case.scope_id, "after"),
                    element_type=RBACElementType.VFOLDER,
                    scope_ref=case.scope_ref,
                    conflict_target=case.conflict_target,
                    additional_scope_refs=case.additional_scope_refs,
                )
            )
            assert result.row.value == "after"
            assert result.row.scope_id == case.scope_id
            entity_id = str(result.row.id)

        async with database_connection.begin_readonly_session() as db_sess:
            rows = (await db_sess.scalars(sa.select(RBACOpsUpsertRow))).all()
            assocs = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()

        assert len(rows) == 1
        assert {_UpsertBinding(a.scope_type, a.scope_id) for a in assocs} == set(
            case.expected_bindings
        )
        assert {a.entity_id for a in assocs} <= {entity_id}

    @pytest.mark.parametrize(
        "seeded_upsert_case",
        [
            _UpsertCase(
                name="user-scope",
                scope_type="user",
                scope_id=_USER_SCOPE_ID,
                scope_ref=_USER_SCOPE_REF,
                conflict_target=ConflictTarget(columns=["name", "scope_type", "scope_id"]),
                additional_scope_refs=[],
                expected_bindings=[_UpsertBinding(PermissionScopeType.USER, _USER_SCOPE_ID)],
            ),
            _UpsertCase(
                name="project-scope-with-additional-user",
                scope_type="project",
                scope_id=_PROJECT_SCOPE_ID,
                scope_ref=_PROJECT_SCOPE_REF,
                conflict_target=ConflictTarget(columns=["name", "scope_type", "scope_id"]),
                additional_scope_refs=[_USER_SCOPE_REF],
                expected_bindings=[
                    _UpsertBinding(PermissionScopeType.PROJECT, _PROJECT_SCOPE_ID),
                    _UpsertBinding(PermissionScopeType.USER, _USER_SCOPE_ID),
                ],
            ),
            _UpsertCase(
                name="public-partial-index",
                scope_type="public",
                scope_id=None,
                scope_ref=None,
                conflict_target=ConflictTarget(
                    columns=["name", "scope_type"],
                    index_predicate=RBACOpsUpsertRow.scope_id.is_(None),
                ),
                additional_scope_refs=[],
                expected_bindings=[],
            ),
        ],
        ids=lambda case: case.name,
        indirect=True,
    )
    async def test_conflict_updates_the_row_and_keeps_its_bindings(
        self,
        provider: RBACOpsProvider,
        database_connection: ExtendedAsyncSAEngine,
        seeded_upsert_case: _UpsertCase,
    ) -> None:
        """A conflicting upsert updates the row in place and leaves its bindings as they were."""
        case = seeded_upsert_case

        async with provider.write_ops() as w:
            result = await w.upsert_scoped(
                RBACEntityUpserter(
                    spec=RBACOpsUpserterSpec(case.scope_type, case.scope_id, "after"),
                    element_type=RBACElementType.VFOLDER,
                    scope_ref=case.scope_ref,
                    conflict_target=case.conflict_target,
                    additional_scope_refs=case.additional_scope_refs,
                )
            )
            assert result.row.id == _UPSERT_EXISTING_ROW_ID
            assert result.row.value == "after"

        async with database_connection.begin_readonly_session() as db_sess:
            rows = (await db_sess.scalars(sa.select(RBACOpsUpsertRow))).all()
            assocs = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()

        assert len(rows) == 1
        assert rows[0].id == _UPSERT_EXISTING_ROW_ID
        assert rows[0].value == "after"
        assert len(assocs) == len(case.expected_bindings)
        assert {_UpsertBinding(a.scope_type, a.scope_id) for a in assocs} == set(
            case.expected_bindings
        )

    async def test_violation_off_the_conflict_target_raises_the_domain_error(
        self,
        provider: RBACOpsProvider,
        upsert_gated_tables: None,
    ) -> None:
        """The conflict target updates; another constraint still maps through the spec."""
        with pytest.raises(_TestUpsertParentMissingError, match="parent does not exist"):
            async with provider.write_ops() as w:
                await w.upsert_scoped(
                    RBACEntityUpserter(
                        spec=RBACOpsGatedUpserterSpec(
                            parent_id=uuid.uuid4(), name=_UPSERT_ENTITY_NAME
                        ),
                        element_type=RBACElementType.VFOLDER,
                        scope_ref=_USER_SCOPE_REF,
                        conflict_target=ConflictTarget(columns=["name"]),
                    )
                )

    async def test_composite_pk_is_rejected(
        self,
        provider: RBACOpsProvider,
        upsert_composite_pk_table: None,
    ) -> None:
        """A composite primary key leaves no single entity id to bind."""
        with pytest.raises(UnsupportedCompositePrimaryKeyError):
            async with provider.write_ops() as w:
                await w.upsert_scoped(
                    RBACEntityUpserter(
                        spec=RBACOpsCompositePKUpserterSpec(),
                        element_type=RBACElementType.VFOLDER,
                        scope_ref=_USER_SCOPE_REF,
                        conflict_target=ConflictTarget(columns=["tenant_id", "item_id"]),
                    )
                )


_ABSENT_PARENT_ID = uuid.uuid4()  # never inserted, so naming it as a parent trips the FK gate


@dataclass(frozen=True)
class _PartialUpsertItem:
    """One batch item: the row it inserts, its scope, and the parent its FK gate checks."""

    row_name: str
    scope_ref: RBACElementRef | None = _USER_SCOPE_REF
    parent_id: UUID | None = None


@dataclass(frozen=True)
class _ExpectedAssocScopeEntity:
    """One association_scopes_entities row the batch must leave, named by the row it binds."""

    row_name: str
    scope_id: str


@dataclass(frozen=True)
class _ScopedPartialUpsertCase:
    """One batch for the partial bulk op: its items, and which land, fail, and bind.

    The expected fields carry no defaults on purpose: every case spells out its full
    outcome, an empty one included.
    """

    name: str
    items: tuple[_PartialUpsertItem, ...]
    expected_succeeded_items: list[str]
    expected_failed_indexes: list[int]
    expected_assoc_scope_entities: list[_ExpectedAssocScopeEntity]


class TestBulkUpsertScopedPartial:
    @pytest.mark.parametrize(
        "case",
        [
            _ScopedPartialUpsertCase(
                name="every-item-lands",
                items=(
                    _PartialUpsertItem(row_name="first"),
                    _PartialUpsertItem(row_name="second"),
                ),
                expected_succeeded_items=["first", "second"],
                expected_failed_indexes=[],
                expected_assoc_scope_entities=[
                    _ExpectedAssocScopeEntity(row_name="first", scope_id=_USER_SCOPE_ID),
                    _ExpectedAssocScopeEntity(row_name="second", scope_id=_USER_SCOPE_ID),
                ],
            ),
            _ScopedPartialUpsertCase(
                name="global-binds-nothing",
                items=(_PartialUpsertItem(row_name="solo", scope_ref=None),),
                expected_succeeded_items=["solo"],
                expected_failed_indexes=[],
                expected_assoc_scope_entities=[],
            ),
            _ScopedPartialUpsertCase(
                name="rejected-item-fails-alone",
                items=(
                    _PartialUpsertItem(row_name="doomed", parent_id=_ABSENT_PARENT_ID),
                    _PartialUpsertItem(row_name="fresh"),
                ),
                expected_succeeded_items=["fresh"],
                expected_failed_indexes=[0],
                expected_assoc_scope_entities=[
                    _ExpectedAssocScopeEntity(row_name="fresh", scope_id=_USER_SCOPE_ID),
                ],
            ),
            _ScopedPartialUpsertCase(
                name="every-item-rejected",
                items=(
                    _PartialUpsertItem(row_name="doomed-a", parent_id=_ABSENT_PARENT_ID),
                    _PartialUpsertItem(row_name="doomed-b", parent_id=_ABSENT_PARENT_ID),
                ),
                expected_succeeded_items=[],
                expected_failed_indexes=[0, 1],
                expected_assoc_scope_entities=[],
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_batch_lands_and_fails_exactly_as_the_case_names(
        self,
        case: _ScopedPartialUpsertCase,
        provider: RBACOpsProvider,
        database_connection: ExtendedAsyncSAEngine,
        upsert_gated_tables: None,
    ) -> None:
        """Each item has its own savepoint: the named items land with their bindings, and a
        rejected one reports its index and leaves neither its row nor its association behind.
        """
        async with provider.write_ops() as w:
            result = await w.bulk_upsert_scoped_partial([
                RBACEntityUpserter(
                    spec=RBACOpsGatedUpserterSpec(parent_id=item.parent_id, name=item.row_name),
                    element_type=RBACElementType.VFOLDER,
                    scope_ref=item.scope_ref,
                    conflict_target=ConflictTarget(columns=["name"]),
                )
                for item in case.items
            ])
            assert [row.name for row in result.items] == case.expected_succeeded_items
            assert [e.index for e in result.failed] == case.expected_failed_indexes
            # Every rejection these batches provoke is the FK gate, mapped by the spec.
            assert all(
                isinstance(e.exception, _TestUpsertParentMissingError) for e in result.failed
            )
            row_ids = {row.name: str(row.id) for row in result.items}

        async with database_connection.begin_readonly_session() as db_sess:
            names = (await db_sess.scalars(sa.select(RBACOpsUpsertGatedRow.name))).all()
            assocs = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()

        assert sorted(names) == sorted(case.expected_succeeded_items)
        assert sorted((a.entity_id, a.scope_id) for a in assocs) == sorted(
            (row_ids[assoc.row_name], assoc.scope_id)
            for assoc in case.expected_assoc_scope_entities
        )


# =============================================================================
# _resolve_scope_template_values
# =============================================================================


@dataclass(frozen=True)
class _ScopeNameSeed:
    """One row per registered scope table, with the display name each must resolve to."""

    domain_ref: ScopeRef
    domain_name: str
    project_ref: ScopeRef
    project_name: str
    resource_group_ref: ScopeRef
    resource_group_name: str
    user_ref: ScopeRef
    username: str


@pytest.fixture
async def scope_name_seed(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[_ScopeNameSeed, None]:
    """A domain, a project, and a user — the scope rows the resolver reads."""
    async with with_tables(
        database_connection,
        [
            # FK dependency order: parents before children
            DomainRow,
            ScalingGroupRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            KeyPairRow,
            GroupRow,
        ],
    ):
        unique = uuid.uuid4().hex[:8]
        domain_id = uuid.uuid4()
        project_id = uuid.uuid4()
        resource_group_id = ResourceGroupID(uuid.uuid4())
        user_id = uuid.uuid4()
        domain_name = f"dom-{unique}"
        project_name = f"proj-{unique}"
        resource_group_name = f"rg-{unique}"
        username = f"user-{unique}"
        async with database_connection.begin_session() as db_sess:
            db_sess.add_all([
                DomainRow(name=domain_name, id=domain_id),
                ScalingGroupRow(
                    id=resource_group_id,
                    name=resource_group_name,
                    driver="static",
                    scheduler="fifo",
                ),
                UserResourcePolicyRow(
                    name=f"urp-{unique}",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                ),
                ProjectResourcePolicyRow(
                    name=f"prp-{unique}",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                ),
            ])
            await db_sess.flush()
            db_sess.add_all([
                GroupRow(
                    id=project_id,
                    name=project_name,
                    domain_name=domain_name,
                    resource_policy=f"prp-{unique}",
                ),
                UserRow(
                    uuid=user_id,
                    username=username,
                    email=f"{username}@example.com",
                    domain_name=domain_name,
                    resource_policy=f"urp-{unique}",
                ),
            ])
        yield _ScopeNameSeed(
            domain_ref=ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=domain_id),
            domain_name=domain_name,
            project_ref=ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id),
            project_name=project_name,
            resource_group_ref=ScopeRef(
                scope_type=RESOURCE_GROUP_SCOPE_TYPE, scope_id=resource_group_id
            ),
            resource_group_name=resource_group_name,
            user_ref=ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=user_id),
            username=username,
        )


class TestResolveScopeTemplateValues:
    """_resolve_scope_template_values maps each ScopeRef to its template values with a
    single UNION ALL query over the registered scope rows."""

    async def test_mixed_scope_types_resolve_to_their_display_names(
        self,
        provider: RBACOpsProvider,
        scope_name_seed: _ScopeNameSeed,
    ) -> None:
        """Domain, project, and resource group resolve to their name, a user to its
        username."""
        seed = scope_name_seed
        refs = [seed.domain_ref, seed.project_ref, seed.resource_group_ref, seed.user_ref]

        async with provider.write_ops() as w:
            result = await w._resolve_scope_template_values(refs)

        assert result == {
            seed.domain_ref: ScopeTemplateValue(
                id=seed.domain_ref.scope_id, name=seed.domain_name, type="domain"
            ),
            seed.project_ref: ScopeTemplateValue(
                id=seed.project_ref.scope_id, name=seed.project_name, type="project"
            ),
            seed.resource_group_ref: ScopeTemplateValue(
                id=seed.resource_group_ref.scope_id,
                name=seed.resource_group_name,
                type="resource_group",
            ),
            seed.user_ref: ScopeTemplateValue(
                id=seed.user_ref.scope_id, name=seed.username, type="user"
            ),
        }

    async def test_unregistered_scope_type_maps_to_none(
        self,
        provider: RBACOpsProvider,
        scope_name_seed: _ScopeNameSeed,
    ) -> None:
        """A scope type without a registered row resolves to None; others still resolve."""
        seed = scope_name_seed
        unregistered = ScopeRef(scope_type=ScopeType("unregistered"), scope_id=uuid.uuid4())

        async with provider.write_ops() as w:
            result = await w._resolve_scope_template_values([unregistered, seed.domain_ref])

        assert result[unregistered] is None
        assert result[seed.domain_ref] is not None

    async def test_missing_row_maps_to_none(
        self,
        provider: RBACOpsProvider,
        scope_name_seed: _ScopeNameSeed,
    ) -> None:
        """A registered scope type whose row does not exist resolves to None."""
        missing = ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=uuid.uuid4())

        async with provider.write_ops() as w:
            result = await w._resolve_scope_template_values([missing])

        assert result == {missing: None}

    async def test_empty_scopes_return_empty_mapping(
        self,
        provider: RBACOpsProvider,
        scope_name_seed: _ScopeNameSeed,
    ) -> None:
        """No scopes -> no query, empty mapping."""
        async with provider.write_ops() as w:
            result = await w._resolve_scope_template_values([])

        assert result == {}
