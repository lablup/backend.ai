"""Integration tests for RBAC entity purger with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.permission.types import OperationType
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    FieldType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.rbac.entity_purger import (
    RBACEntity,
    RBACEntityBatchPurger,
    RBACEntityBatchPurgerResult,
    RBACEntityBatchPurgerSpec,
    RBACEntityPurger,
    RBACEntityPurgerResult,
    RBACEntityPurgerSpec,
    execute_rbac_entity_batch_purger,
    execute_rbac_entity_purger,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Row Models
# =============================================================================


class RBACEntityPurgerTestRow(Base):
    """ORM model implementing RBACEntityRowProtocol for entity purger testing."""

    __tablename__ = "test_rbac_purger"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    owner_scope_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    owner_scope_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    def scope_id(self) -> ScopeId:
        return ScopeId(scope_type=ScopeType(self.owner_scope_type), scope_id=self.owner_scope_id)

    def entity_id(self) -> ObjectId:
        return ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(self.id))


# =============================================================================
# Purger Spec Implementations
# =============================================================================


class SimpleRBACEntityPurgerSpec(RBACEntityPurgerSpec):
    """Simple spec for entity purger testing."""

    def __init__(self, entity_uuid: UUID) -> None:
        self._entity_uuid = entity_uuid

    def entity(self) -> RBACEntity:
        return RBACEntity(
            entity=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(self._entity_uuid))
        )


# =============================================================================
# Tables List
# =============================================================================

ENTITY_PURGER_TABLES = [
    RBACEntityPurgerTestRow,
    RoleRow,
    PermissionGroupRow,
    PermissionRow,
    ObjectPermissionRow,
    AssociationScopesEntitiesRow,
    EntityFieldRow,
]


# =============================================================================
# Data Classes for Fixtures
# =============================================================================


@dataclass
class EntityWithAssociationContext:
    """Context with entity row and scope association."""

    entity_uuid: UUID
    user_id: str


@dataclass
class EntityWithRoleAndPermissionsContext:
    """Context with entity, role, permission group, and object permissions."""

    entity_uuid: UUID
    user_id: str
    role_id: UUID
    perm_group_id: UUID


@dataclass
class TwoEntitiesContext:
    """Context with two entities sharing same scope."""

    entity_uuid1: UUID
    entity_uuid2: UUID
    user_id: str
    role_id: UUID


@dataclass
class MultiScopeEntityContext:
    """Context with entity shared across multiple scopes."""

    entity_uuid: UUID
    owner_user_id: str
    shared_user_id: str


@dataclass
class EntityWithUnrelatedEntityContext:
    """Context with one entity having role's object_permission and another unrelated entity in same scope."""

    entity_uuid: UUID  # Entity with role's object_permission
    unrelated_entity_uuid: UUID  # Entity without role's object_permission
    user_id: str
    role_id: UUID
    perm_group_id: UUID


@dataclass
class EntityWithPermissionRowContext:
    """Context with entity that has PermissionRow in its permission group."""

    entity_uuid: UUID
    user_id: str
    role_id: UUID
    perm_group_id: UUID


@dataclass
class TwoRolesOneEntityContext:
    """Context with two roles having object_permission for the same entity.

    Scenario:
    - roleA: object_permission(vfolderA), permission_group(scopeA)
    - roleB: object_permission(vfolderA, vfolderB), permission_group(scopeA)
    - vfolderA, vfolderB both in scopeA

    When vfolderA is purged:
    - roleA's permission_group(scopeA) should be DELETED (no other entity)
    - roleB's permission_group(scopeA) should be PRESERVED (vfolderB remains)
    """

    vfolder_a_uuid: UUID
    vfolder_b_uuid: UUID
    user_id: str
    role_a_id: UUID
    role_b_id: UUID
    perm_group_a_id: UUID
    perm_group_b_id: UUID


@dataclass
class BatchEntitiesContext:
    """Context with multiple entities for batch purge testing."""

    entity_uuids: list[UUID]
    user_id: str


@dataclass
class BatchEntitiesWithPermissionsContext:
    """Context with multiple entities and shared role/permissions."""

    entity_uuids: list[UUID]
    user_id: str
    role_id: UUID
    perm_group_id: UUID


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC entity purger test tables."""
    async with with_tables(database_connection, ENTITY_PURGER_TABLES):  # type: ignore[arg-type]
        yield


# =============================================================================
# Tests
# =============================================================================


class TestRBACEntityPurgerBasic:
    """Basic tests for entity purger operations."""

    @pytest.fixture
    async def entity_with_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithAssociationContext, None]:
        """Create entity row and scope association."""
        user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()

        async with database_connection.begin_session_read_committed() as db_sess:
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="test-entity",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(entity_row)

            assoc_row = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
            )
            db_sess.add(assoc_row)
            await db_sess.flush()

        yield EntityWithAssociationContext(
            entity_uuid=entity_uuid,
            user_id=user_id,
        )

    async def test_purger_deletes_main_row_and_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_association: EntityWithAssociationContext,
    ) -> None:
        """Test that purger deletes main row and scope-entity association."""
        ctx = entity_with_association

        async with database_connection.begin_session_read_committed() as db_sess:
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            result = await execute_rbac_entity_purger(db_sess, purger)

            # Verify result
            assert isinstance(result, RBACEntityPurgerResult)
            assert result.row.id == ctx.entity_uuid
            assert result.row.name == "test-entity"

            # Verify main row deleted
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityPurgerTestRow)
            )
            assert entity_count == 0

            # Verify association deleted
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0

    async def test_purger_returns_none_for_nonexistent_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that purger returns None when row doesn't exist."""
        nonexistent_uuid = uuid.uuid4()

        async with database_connection.begin_session_read_committed() as db_sess:
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=nonexistent_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=nonexistent_uuid,
                spec=spec,
            )
            result = await execute_rbac_entity_purger(db_sess, purger)
            assert result is None


class TestRBACEntityPurgerWithObjectPermissions:
    """Tests for entity purger with object permissions cleanup."""

    @pytest.fixture
    async def entity_with_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithRoleAndPermissionsContext, None]:
        """Create entity with role, permission group, and object permissions."""
        user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()
        role_id: UUID
        perm_group_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="test-entity",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(entity_row)

            assoc_row = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
            )
            db_sess.add(assoc_row)

            role = RoleRow(
                id=uuid.uuid4(),
                name="system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            perm_group = PermissionGroupRow(
                role_id=role.id,
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            db_sess.add(perm_group)
            await db_sess.flush()

            for op in [OperationType.READ, OperationType.UPDATE]:
                obj_perm = ObjectPermissionRow(
                    role_id=role.id,
                    permission_group_id=perm_group.id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                    operation=op,
                )
                db_sess.add(obj_perm)
            await db_sess.flush()

            role_id = role.id
            perm_group_id = perm_group.id

        yield EntityWithRoleAndPermissionsContext(
            entity_uuid=entity_uuid,
            user_id=user_id,
            role_id=role_id,
            perm_group_id=perm_group_id,
        )

    @pytest.fixture
    async def two_entities_with_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[TwoEntitiesContext, None]:
        """Create two entities with shared role and separate object permissions."""
        user_id = str(uuid.uuid4())
        entity_uuid1 = uuid.uuid4()
        entity_uuid2 = uuid.uuid4()
        role_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            for entity_uuid, name in [(entity_uuid1, "entity-1"), (entity_uuid2, "entity-2")]:
                entity_row = RBACEntityPurgerTestRow(
                    id=entity_uuid,
                    name=name,
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                )
                db_sess.add(entity_row)

                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)

            role = RoleRow(
                id=uuid.uuid4(),
                name="system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            perm_group = PermissionGroupRow(
                role_id=role.id,
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            db_sess.add(perm_group)
            await db_sess.flush()

            for entity_uuid in [entity_uuid1, entity_uuid2]:
                obj_perm = ObjectPermissionRow(
                    role_id=role.id,
                    permission_group_id=perm_group.id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                    operation=OperationType.READ,
                )
                db_sess.add(obj_perm)
            await db_sess.flush()

            role_id = role.id

        yield TwoEntitiesContext(
            entity_uuid1=entity_uuid1,
            entity_uuid2=entity_uuid2,
            user_id=user_id,
            role_id=role_id,
        )

    async def test_purger_deletes_object_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_permissions: EntityWithRoleAndPermissionsContext,
    ) -> None:
        """Test that purger deletes related object permissions."""
        ctx = entity_with_permissions

        async with database_connection.begin_session_read_committed() as db_sess:
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify object permissions deleted
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 0

    async def test_purger_preserves_unrelated_object_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_entities_with_permissions: TwoEntitiesContext,
    ) -> None:
        """Test that purger preserves object permissions for other entities."""
        ctx = two_entities_with_permissions

        async with database_connection.begin_session_read_committed() as db_sess:
            # Delete only entity1
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid1)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid1,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify only entity1's permissions deleted
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 1

            # Verify entity2's permission preserved
            remaining_perm = await db_sess.scalar(sa.select(ObjectPermissionRow))
            assert remaining_perm is not None
            assert remaining_perm.entity_id == str(ctx.entity_uuid2)


class TestRBACEntityPurgerPermissionGroupCleanup:
    """Tests for permission group cleanup during entity purging."""

    @pytest.fixture
    async def single_entity_with_empty_perm_group(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithRoleAndPermissionsContext, None]:
        """Create single entity with empty permission group (no PermissionRow)."""
        user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()
        role_id: UUID
        perm_group_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="test-entity",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(entity_row)

            assoc_row = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
            )
            db_sess.add(assoc_row)

            role = RoleRow(
                id=uuid.uuid4(),
                name="system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            perm_group = PermissionGroupRow(
                role_id=role.id,
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            db_sess.add(perm_group)
            await db_sess.flush()

            # Create object permission (but no PermissionRow)
            obj_perm = ObjectPermissionRow(
                role_id=role.id,
                permission_group_id=perm_group.id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
                operation=OperationType.READ,
            )
            db_sess.add(obj_perm)
            await db_sess.flush()

            role_id = role.id
            perm_group_id = perm_group.id

        yield EntityWithRoleAndPermissionsContext(
            entity_uuid=entity_uuid,
            user_id=user_id,
            role_id=role_id,
            perm_group_id=perm_group_id,
        )

    @pytest.fixture
    async def two_entities_with_empty_perm_group(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[TwoEntitiesContext, None]:
        """Create two entities with shared empty permission group."""
        user_id = str(uuid.uuid4())
        entity_uuid1 = uuid.uuid4()
        entity_uuid2 = uuid.uuid4()
        role_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            for entity_uuid, name in [(entity_uuid1, "entity-1"), (entity_uuid2, "entity-2")]:
                entity_row = RBACEntityPurgerTestRow(
                    id=entity_uuid,
                    name=name,
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                )
                db_sess.add(entity_row)

                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)

            role = RoleRow(
                id=uuid.uuid4(),
                name="system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            perm_group = PermissionGroupRow(
                role_id=role.id,
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            db_sess.add(perm_group)
            await db_sess.flush()

            for entity_uuid in [entity_uuid1, entity_uuid2]:
                obj_perm = ObjectPermissionRow(
                    role_id=role.id,
                    permission_group_id=perm_group.id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                    operation=OperationType.READ,
                )
                db_sess.add(obj_perm)
            await db_sess.flush()

            role_id = role.id

        yield TwoEntitiesContext(
            entity_uuid1=entity_uuid1,
            entity_uuid2=entity_uuid2,
            user_id=user_id,
            role_id=role_id,
        )

    async def test_purger_deletes_empty_permission_group(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_entity_with_empty_perm_group: EntityWithRoleAndPermissionsContext,
    ) -> None:
        """Test that purger deletes permission groups with no remaining permissions."""
        ctx = single_entity_with_empty_perm_group

        async with database_connection.begin_session_read_committed() as db_sess:
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify empty permission group deleted
            perm_group_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionGroupRow)
            )
            assert perm_group_count == 0

    async def test_purger_preserves_permission_group_with_other_entities(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_entities_with_empty_perm_group: TwoEntitiesContext,
    ) -> None:
        """Test that purger preserves permission groups that have other scoped entities."""
        ctx = two_entities_with_empty_perm_group

        async with database_connection.begin_session_read_committed() as db_sess:
            # Delete entity1
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid1)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid1,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify permission group preserved (entity2 still has object_permission with same role)
            perm_group_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionGroupRow)
            )
            assert perm_group_count == 1

    @pytest.fixture
    async def entity_with_unrelated_entity_in_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithUnrelatedEntityContext, None]:
        """Create two entities in same scope, but only one has role's object_permission.

        Scenario:
        - entity1: has object_permission with Role R
        - entity2: in same scope but NO object_permission with Role R
        - Role R has permission_group for this scope

        When entity1 is deleted:
        - permission_group should be DELETED (role has no other object_permission in scope)
        """
        user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()
        unrelated_entity_uuid = uuid.uuid4()
        role_id: UUID
        perm_group_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            # Create entity with role's object_permission
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="entity-with-permission",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(entity_row)

            assoc_row = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
            )
            db_sess.add(assoc_row)

            # Create unrelated entity (same scope, but no role permission)
            unrelated_entity_row = RBACEntityPurgerTestRow(
                id=unrelated_entity_uuid,
                name="unrelated-entity",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(unrelated_entity_row)

            unrelated_assoc_row = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(unrelated_entity_uuid),
            )
            db_sess.add(unrelated_assoc_row)

            # Create role and permission group
            role = RoleRow(
                id=uuid.uuid4(),
                name="system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            perm_group = PermissionGroupRow(
                role_id=role.id,
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            db_sess.add(perm_group)
            await db_sess.flush()

            # Create object permission ONLY for entity (not unrelated_entity)
            obj_perm = ObjectPermissionRow(
                role_id=role.id,
                permission_group_id=perm_group.id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
                operation=OperationType.READ,
            )
            db_sess.add(obj_perm)
            await db_sess.flush()

            role_id = role.id
            perm_group_id = perm_group.id

        yield EntityWithUnrelatedEntityContext(
            entity_uuid=entity_uuid,
            unrelated_entity_uuid=unrelated_entity_uuid,
            user_id=user_id,
            role_id=role_id,
            perm_group_id=perm_group_id,
        )

    async def test_purger_deletes_permission_group_when_other_entity_has_no_role_permission(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_unrelated_entity_in_scope: EntityWithUnrelatedEntityContext,
    ) -> None:
        """Test that purger deletes permission group when other entities in scope have no role permission.

        This tests the scenario where:
        - Entity A has object_permission with Role R
        - Entity B is in the same scope but has NO object_permission with Role R
        - When Entity A is deleted, permission_group should be deleted
          (because Role R has no other object_permission in that scope)
        """
        ctx = entity_with_unrelated_entity_in_scope

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state: unrelated entity exists in same scope
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2  # Both entities have associations

            # Delete entity with role's object_permission
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify permission group is DELETED
            # (even though unrelated entity exists in same scope,
            #  the role has no other object_permission in this scope)
            perm_group_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionGroupRow)
            )
            assert perm_group_count == 0

            # Verify unrelated entity and its association are preserved
            remaining_entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityPurgerTestRow)
            )
            assert remaining_entity_count == 1

            remaining_assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert remaining_assoc_count == 1


class TestRBACEntityPurgerMultipleRoles:
    """Tests for entity purger with multiple roles having permissions for the same entity."""

    @pytest.fixture
    async def two_roles_one_entity(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[TwoRolesOneEntityContext, None]:
        """Create two roles with object_permissions for overlapping entities.

        Setup:
        - vfolderA in scopeA
        - vfolderB in scopeA
        - roleA: object_permission(vfolderA), permission_group(scopeA)
        - roleB: object_permission(vfolderA, vfolderB), permission_group(scopeA)
        """
        user_id = str(uuid.uuid4())
        vfolder_a_uuid = uuid.uuid4()
        vfolder_b_uuid = uuid.uuid4()

        async with database_connection.begin_session_read_committed() as db_sess:
            # Create vfolderA and vfolderB
            for entity_uuid, name in [
                (vfolder_a_uuid, "vfolder-a"),
                (vfolder_b_uuid, "vfolder-b"),
            ]:
                entity_row = RBACEntityPurgerTestRow(
                    id=entity_uuid,
                    name=name,
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                )
                db_sess.add(entity_row)

                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)

            # Create roleA: only has object_permission for vfolderA
            role_a = RoleRow(
                id=uuid.uuid4(),
                name="role-a",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role_a)

            # Create roleB: has object_permission for both vfolderA and vfolderB
            role_b = RoleRow(
                id=uuid.uuid4(),
                name="role-b",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role_b)
            await db_sess.flush()

            # Create permission_group for roleA
            perm_group_a = PermissionGroupRow(
                role_id=role_a.id,
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            db_sess.add(perm_group_a)

            # Create permission_group for roleB
            perm_group_b = PermissionGroupRow(
                role_id=role_b.id,
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            db_sess.add(perm_group_b)
            await db_sess.flush()

            # roleA: object_permission for vfolderA only
            obj_perm_a = ObjectPermissionRow(
                role_id=role_a.id,
                permission_group_id=perm_group_a.id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(vfolder_a_uuid),
                operation=OperationType.READ,
            )
            db_sess.add(obj_perm_a)

            # roleB: object_permission for vfolderA
            obj_perm_b1 = ObjectPermissionRow(
                role_id=role_b.id,
                permission_group_id=perm_group_b.id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(vfolder_a_uuid),
                operation=OperationType.READ,
            )
            db_sess.add(obj_perm_b1)

            # roleB: object_permission for vfolderB
            obj_perm_b2 = ObjectPermissionRow(
                role_id=role_b.id,
                permission_group_id=perm_group_b.id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(vfolder_b_uuid),
                operation=OperationType.READ,
            )
            db_sess.add(obj_perm_b2)
            await db_sess.flush()

        yield TwoRolesOneEntityContext(
            vfolder_a_uuid=vfolder_a_uuid,
            vfolder_b_uuid=vfolder_b_uuid,
            user_id=user_id,
            role_a_id=role_a.id,
            role_b_id=role_b.id,
            perm_group_a_id=perm_group_a.id,
            perm_group_b_id=perm_group_b.id,
        )

    async def test_purger_handles_multiple_roles_independently(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_roles_one_entity: TwoRolesOneEntityContext,
    ) -> None:
        """Test that purger evaluates permission_group deletion per-role independently.

        When vfolderA is purged:
        - roleA's permission_group should be DELETED (roleA has no other entity in scopeA)
        - roleB's permission_group should be PRESERVED (roleB still has vfolderB in scopeA)
        """
        ctx = two_roles_one_entity

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state
            perm_group_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionGroupRow)
            )
            assert perm_group_count == 2

            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 3  # roleA:1 + roleB:2

            # Purge vfolderA
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.vfolder_a_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.vfolder_a_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify roleA's permission_group is DELETED
            role_a_perm_group = await db_sess.scalar(
                sa.select(PermissionGroupRow).where(PermissionGroupRow.role_id == ctx.role_a_id)
            )
            assert role_a_perm_group is None

            # Verify roleB's permission_group is PRESERVED
            role_b_perm_group = await db_sess.scalar(
                sa.select(PermissionGroupRow).where(PermissionGroupRow.role_id == ctx.role_b_id)
            )
            assert role_b_perm_group is not None
            assert role_b_perm_group.id == ctx.perm_group_b_id

            # Verify object_permissions: only roleB's vfolderB permission remains
            remaining_obj_perms = (await db_sess.scalars(sa.select(ObjectPermissionRow))).all()
            assert len(remaining_obj_perms) == 1
            assert remaining_obj_perms[0].role_id == ctx.role_b_id
            assert remaining_obj_perms[0].entity_id == str(ctx.vfolder_b_uuid)


class TestRBACEntityPurgerMultipleScopes:
    """Tests for entity purger with entities shared across multiple scopes."""

    @pytest.fixture
    async def multi_scope_entity(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[MultiScopeEntityContext, None]:
        """Create entity shared across multiple scopes."""
        owner_user_id = str(uuid.uuid4())
        shared_user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()

        async with database_connection.begin_session_read_committed() as db_sess:
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="shared-entity",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=owner_user_id,
            )
            db_sess.add(entity_row)

            # Create associations for both owner and shared user
            for user_id in [owner_user_id, shared_user_id]:
                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)
            await db_sess.flush()

        yield MultiScopeEntityContext(
            entity_uuid=entity_uuid,
            owner_user_id=owner_user_id,
            shared_user_id=shared_user_id,
        )

    async def test_purger_deletes_all_scope_associations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        multi_scope_entity: MultiScopeEntityContext,
    ) -> None:
        """Test that purger deletes associations across all scopes."""
        ctx = multi_scope_entity

        async with database_connection.begin_session_read_committed() as db_sess:
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify all associations deleted
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0


class TestRBACEntityPurgerEntityFieldCleanup:
    """Tests for EntityFieldRow cleanup during entity purging."""

    @dataclass
    class EntityWithFieldsContext:
        """Context with entity and its field mappings."""

        entity_uuid: UUID
        user_id: str
        field_ids: list[str]

    @dataclass
    class TwoEntitiesWithFieldsContext:
        """Context with two entities having field mappings."""

        entity_uuid1: UUID
        entity_uuid2: UUID
        user_id: str
        entity1_field_ids: list[str]
        entity2_field_ids: list[str]

    @pytest.fixture
    async def entity_with_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithFieldsContext, None]:
        """Create entity with multiple EntityFieldRow mappings."""
        user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()
        field_ids = [str(uuid.uuid4()) for _ in range(3)]

        async with database_connection.begin_session_read_committed() as db_sess:
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="entity-with-fields",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(entity_row)

            assoc_row = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
            )
            db_sess.add(assoc_row)

            # Create EntityFieldRows for this entity
            for field_id in field_ids:
                entity_field = EntityFieldRow(
                    entity_type=EntityType.VFOLDER.value,
                    entity_id=str(entity_uuid),
                    field_type=FieldType.KERNEL.value,
                    field_id=field_id,
                )
                db_sess.add(entity_field)
            await db_sess.flush()

        yield self.EntityWithFieldsContext(
            entity_uuid=entity_uuid,
            user_id=user_id,
            field_ids=field_ids,
        )

    @pytest.fixture
    async def two_entities_with_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[TwoEntitiesWithFieldsContext, None]:
        """Create two entities each with EntityFieldRow mappings."""
        user_id = str(uuid.uuid4())
        entity_uuid1 = uuid.uuid4()
        entity_uuid2 = uuid.uuid4()
        entity1_field_ids = [str(uuid.uuid4()) for _ in range(2)]
        entity2_field_ids = [str(uuid.uuid4()) for _ in range(2)]

        async with database_connection.begin_session_read_committed() as db_sess:
            for entity_uuid, name in [
                (entity_uuid1, "entity-1"),
                (entity_uuid2, "entity-2"),
            ]:
                entity_row = RBACEntityPurgerTestRow(
                    id=entity_uuid,
                    name=name,
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                )
                db_sess.add(entity_row)

                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)

            # Create EntityFieldRows for entity1
            for field_id in entity1_field_ids:
                entity_field = EntityFieldRow(
                    entity_type=EntityType.VFOLDER.value,
                    entity_id=str(entity_uuid1),
                    field_type=FieldType.KERNEL.value,
                    field_id=field_id,
                )
                db_sess.add(entity_field)

            # Create EntityFieldRows for entity2
            for field_id in entity2_field_ids:
                entity_field = EntityFieldRow(
                    entity_type=EntityType.VFOLDER.value,
                    entity_id=str(entity_uuid2),
                    field_type=FieldType.KERNEL.value,
                    field_id=field_id,
                )
                db_sess.add(entity_field)
            await db_sess.flush()

        yield self.TwoEntitiesWithFieldsContext(
            entity_uuid1=entity_uuid1,
            entity_uuid2=entity_uuid2,
            user_id=user_id,
            entity1_field_ids=entity1_field_ids,
            entity2_field_ids=entity2_field_ids,
        )

    async def test_purger_deletes_entity_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_fields: EntityWithFieldsContext,
    ) -> None:
        """Test that purger deletes all EntityFieldRows for the entity."""
        ctx = entity_with_fields

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_field_count == 3

            # Execute purge
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify all EntityFieldRows deleted
            remaining_entity_fields = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert remaining_entity_fields == 0

    async def test_purger_preserves_other_entity_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_entities_with_fields: TwoEntitiesWithFieldsContext,
    ) -> None:
        """Test that purger preserves EntityFieldRows for other entities."""
        ctx = two_entities_with_fields

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_field_count == 4  # 2 + 2

            # Delete only entity1
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid1)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid1,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify only entity1's fields deleted
            remaining_entity_fields = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert remaining_entity_fields == 2

            # Verify entity2's fields preserved
            remaining_fields = (await db_sess.scalars(sa.select(EntityFieldRow))).all()
            assert all(f.entity_id == str(ctx.entity_uuid2) for f in remaining_fields)


class TestRBACEntityPurgerPermissionRowPreservation:
    """Tests for permission group preservation when PermissionRow exists."""

    @pytest.fixture
    async def entity_with_permission_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithPermissionRowContext, None]:
        """Create entity with permission group that has PermissionRow (type-level permission).

        Scenario:
        - Entity A with object_permission
        - PermissionGroup has PermissionRow (type-level permission for VFOLDER)

        When Entity A is deleted:
        - PermissionGroup should be PRESERVED (has remaining PermissionRow)
        """
        user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()
        role_id: UUID
        perm_group_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="entity-with-perm-row",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(entity_row)

            assoc_row = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
            )
            db_sess.add(assoc_row)

            role = RoleRow(
                id=uuid.uuid4(),
                name="system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            perm_group = PermissionGroupRow(
                role_id=role.id,
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            db_sess.add(perm_group)
            await db_sess.flush()

            # Create PermissionRow (type-level permission) in the permission group
            perm_row = PermissionRow(
                permission_group_id=perm_group.id,
                entity_type=EntityType.VFOLDER,
                operation=OperationType.READ,
            )
            db_sess.add(perm_row)

            # Create object permission for the entity
            obj_perm = ObjectPermissionRow(
                role_id=role.id,
                permission_group_id=perm_group.id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
                operation=OperationType.READ,
            )
            db_sess.add(obj_perm)
            await db_sess.flush()

            role_id = role.id
            perm_group_id = perm_group.id

        yield EntityWithPermissionRowContext(
            entity_uuid=entity_uuid,
            user_id=user_id,
            role_id=role_id,
            perm_group_id=perm_group_id,
        )

    async def test_purger_preserves_permission_group_with_remaining_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_permission_row: EntityWithPermissionRowContext,
    ) -> None:
        """Test that purger preserves permission groups that have remaining PermissionRow entries.

        When an entity is deleted, permission groups should NOT be deleted if they
        still have type-level permissions (PermissionRow entries).
        """
        ctx = entity_with_permission_row

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state
            perm_row_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionRow)
            )
            assert perm_row_count == 1

            perm_group_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionGroupRow)
            )
            assert perm_group_count == 1

            # Delete the entity
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify object permission is deleted
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 0

            # Verify permission group is PRESERVED (has PermissionRow)
            remaining_perm_group_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionGroupRow)
            )
            assert remaining_perm_group_count == 1

            remaining_perm_group = await db_sess.scalar(sa.select(PermissionGroupRow))
            assert remaining_perm_group is not None
            assert remaining_perm_group.id == ctx.perm_group_id

            # Verify PermissionRow is preserved
            remaining_perm_row_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionRow)
            )
            assert remaining_perm_row_count == 1


# =============================================================================
# Batch Purger Tests
# =============================================================================


class TestEntityBatchPurgerSpec(RBACEntityBatchPurgerSpec[RBACEntityPurgerTestRow]):
    """Test spec for batch purging entities."""

    def build_subquery(self) -> sa.sql.Select[tuple[RBACEntityPurgerTestRow]]:
        return sa.select(RBACEntityPurgerTestRow)

    def entity_type(self) -> EntityType:
        return EntityType.VFOLDER


class TestRBACEntityBatchPurger:
    """Tests for RBAC entity batch purger operations."""

    @pytest.fixture
    async def batch_entities(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[BatchEntitiesContext, None]:
        """Create multiple entities with scope associations."""
        user_id = str(uuid.uuid4())
        entity_uuids = [uuid.uuid4() for _ in range(5)]

        async with database_connection.begin_session_read_committed() as db_sess:
            for i, entity_uuid in enumerate(entity_uuids):
                entity_row = RBACEntityPurgerTestRow(
                    id=entity_uuid,
                    name=f"entity-{i}",
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                )
                db_sess.add(entity_row)

                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)
            await db_sess.flush()

        yield BatchEntitiesContext(
            entity_uuids=entity_uuids,
            user_id=user_id,
        )

    @pytest.fixture
    async def batch_entities_with_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[BatchEntitiesWithPermissionsContext, None]:
        """Create multiple entities with shared role and object permissions."""
        user_id = str(uuid.uuid4())
        entity_uuids = [uuid.uuid4() for _ in range(3)]
        role_id: UUID
        perm_group_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            for i, entity_uuid in enumerate(entity_uuids):
                entity_row = RBACEntityPurgerTestRow(
                    id=entity_uuid,
                    name=f"entity-{i}",
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                )
                db_sess.add(entity_row)

                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)

            # Create role
            role = RoleRow(
                id=uuid.uuid4(),
                name="batch-test-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            # Create permission group
            perm_group = PermissionGroupRow(
                role_id=role.id,
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            db_sess.add(perm_group)
            await db_sess.flush()

            # Create object permissions for all entities
            for entity_uuid in entity_uuids:
                obj_perm = ObjectPermissionRow(
                    role_id=role.id,
                    permission_group_id=perm_group.id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                    operation=OperationType.READ,
                )
                db_sess.add(obj_perm)
            await db_sess.flush()

            role_id = role.id
            perm_group_id = perm_group.id

        yield BatchEntitiesWithPermissionsContext(
            entity_uuids=entity_uuids,
            user_id=user_id,
            role_id=role_id,
            perm_group_id=perm_group_id,
        )

    async def test_batch_purger_deletes_multiple_entities(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_entities: BatchEntitiesContext,
    ) -> None:
        """Test that batch purger deletes all entities and their associations."""

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityPurgerTestRow)
            )
            assert entity_count == 5

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 5

            # Execute batch purge
            spec = TestEntityBatchPurgerSpec()
            purger: RBACEntityBatchPurger[RBACEntityPurgerTestRow] = RBACEntityBatchPurger(
                spec=spec
            )
            result = await execute_rbac_entity_batch_purger(db_sess, purger)

            # Verify result
            assert isinstance(result, RBACEntityBatchPurgerResult)
            assert result.deleted_count == 5
            assert result.deleted_scope_association_count == 5
            assert result.deleted_object_permission_count == 0
            assert result.deleted_permission_group_count == 0

            # Verify all entities deleted
            remaining_entities = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityPurgerTestRow)
            )
            assert remaining_entities == 0

            # Verify all associations deleted
            remaining_assocs = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert remaining_assocs == 0

    async def test_batch_purger_cleans_rbac_entries(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_entities_with_permissions: BatchEntitiesWithPermissionsContext,
    ) -> None:
        """Test that batch purger cleans up object permissions and orphaned permission groups."""

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 3

            perm_group_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionGroupRow)
            )
            assert perm_group_count == 1

            # Execute batch purge
            spec = TestEntityBatchPurgerSpec()
            purger: RBACEntityBatchPurger[RBACEntityPurgerTestRow] = RBACEntityBatchPurger(
                spec=spec
            )
            result = await execute_rbac_entity_batch_purger(db_sess, purger)

            # Verify result
            assert result.deleted_count == 3
            assert result.deleted_object_permission_count == 3
            assert result.deleted_permission_group_count == 1  # Orphaned after all entities deleted
            assert result.deleted_scope_association_count == 3

            # Verify object permissions deleted
            remaining_obj_perms = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert remaining_obj_perms == 0

            # Verify orphaned permission group deleted
            remaining_perm_groups = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionGroupRow)
            )
            assert remaining_perm_groups == 0

    async def test_batch_purger_handles_empty_batch(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that batch purger handles empty results gracefully."""
        async with database_connection.begin_session_read_committed() as db_sess:
            spec = TestEntityBatchPurgerSpec()
            purger: RBACEntityBatchPurger[RBACEntityPurgerTestRow] = RBACEntityBatchPurger(
                spec=spec
            )
            result = await execute_rbac_entity_batch_purger(db_sess, purger)

            assert isinstance(result, RBACEntityBatchPurgerResult)
            assert result.deleted_count == 0
            assert result.deleted_object_permission_count == 0
            assert result.deleted_permission_group_count == 0
            assert result.deleted_scope_association_count == 0

    async def test_batch_purger_respects_batch_size(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_entities: BatchEntitiesContext,
    ) -> None:
        """Test that batch purger processes in batches according to batch_size."""

        async with database_connection.begin_session_read_committed() as db_sess:
            # Execute batch purge with small batch size
            spec = TestEntityBatchPurgerSpec()
            purger: RBACEntityBatchPurger[RBACEntityPurgerTestRow] = RBACEntityBatchPurger(
                spec=spec,
                batch_size=2,  # Small batch size to force multiple iterations
            )
            result = await execute_rbac_entity_batch_purger(db_sess, purger)

            # Should still delete all 5 entities across multiple batches
            assert result.deleted_count == 5
            assert result.deleted_scope_association_count == 5

            # Verify all entities deleted
            remaining_entities = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityPurgerTestRow)
            )
            assert remaining_entities == 0


# =============================================================================
# Composite Primary Key Tests
# =============================================================================


class CompositePKPurgerTestRow(Base):
    """ORM model with composite primary key for testing rejection."""

    __tablename__ = "test_rbac_purger_composite_pk"
    __table_args__ = {"extend_existing": True}

    tenant_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)


class CompositePKPurgerSpec(RBACEntityPurgerSpec):
    """Purger spec for composite PK testing."""

    def __init__(self, entity_uuid: str) -> None:
        self._entity_uuid = entity_uuid

    def entity(self) -> RBACEntity:
        return RBACEntity(
            entity=ObjectId(entity_type=EntityType.VFOLDER, entity_id=self._entity_uuid)
        )


class CompositePKBatchPurgerSpec(RBACEntityBatchPurgerSpec[CompositePKPurgerTestRow]):
    """Batch purger spec for composite PK testing."""

    def build_subquery(self) -> sa.Select:
        return sa.select(CompositePKPurgerTestRow)

    def entity_type(self) -> EntityType:
        return EntityType.VFOLDER


class TestRBACEntityPurgerCompositePK:
    """Tests for composite primary key rejection in RBAC entity purger."""

    async def test_single_purger_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that single entity purger rejects composite PK tables."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: CompositePKPurgerTestRow.__table__.create(c, checkfirst=True)
            )

        try:
            async with database_connection.begin_session_read_committed() as db_sess:
                spec = CompositePKPurgerSpec(entity_uuid="test-123")
                purger = RBACEntityPurger(
                    row_class=CompositePKPurgerTestRow,
                    pk_value=1,  # PK value (error raised before lookup due to composite PK)
                    spec=spec,
                )

                with pytest.raises(UnsupportedCompositePrimaryKeyError):
                    await execute_rbac_entity_purger(db_sess, purger)
        finally:
            async with database_connection.begin() as conn:
                await conn.run_sync(
                    lambda c: CompositePKPurgerTestRow.__table__.drop(c, checkfirst=True)
                )

    async def test_batch_purger_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that batch entity purger rejects composite PK tables."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: CompositePKPurgerTestRow.__table__.create(c, checkfirst=True)
            )

        try:
            async with database_connection.begin_session_read_committed() as db_sess:
                spec = CompositePKBatchPurgerSpec()
                purger = RBACEntityBatchPurger(spec=spec)

                with pytest.raises(UnsupportedCompositePrimaryKeyError):
                    await execute_rbac_entity_batch_purger(db_sess, purger)
        finally:
            async with database_connection.begin() as conn:
                await conn.run_sync(
                    lambda c: CompositePKPurgerTestRow.__table__.drop(c, checkfirst=True)
                )
