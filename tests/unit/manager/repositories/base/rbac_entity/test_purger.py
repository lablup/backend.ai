"""Integration tests for RBAC entity purger with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from ai.backend.common.data.permission.types import OperationType
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.rbac_entity.purger import (
    Purger,
    PurgerResult,
    execute_purger,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Row Models
# =============================================================================


class RBACPurgerTestRow(Base):
    """ORM model implementing RBACEntityRow for purger testing."""

    __tablename__ = "test_rbac_purger"
    __table_args__ = {"extend_existing": True}

    id: UUID = sa.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: str = sa.Column(sa.String(50), nullable=False)
    owner_scope_type: str = sa.Column(sa.String(32), nullable=False)
    owner_scope_id: str = sa.Column(sa.String(64), nullable=False)

    def scope_id(self) -> ScopeId:
        return ScopeId(scope_type=ScopeType(self.owner_scope_type), scope_id=self.owner_scope_id)

    def entity_id(self) -> ObjectId:
        return ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(self.id))

    def field_id(self) -> ObjectId | None:
        return None


class RBACPurgerFieldTestRow(Base):
    """ORM model for field-scoped entity purger testing."""

    __tablename__ = "test_rbac_purger_field"
    __table_args__ = {"extend_existing": True}

    id: UUID = sa.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: str = sa.Column(sa.String(50), nullable=False)
    owner_scope_type: str = sa.Column(sa.String(32), nullable=False)
    owner_scope_id: str = sa.Column(sa.String(64), nullable=False)
    parent_entity_id: str = sa.Column(sa.String(64), nullable=False)

    def scope_id(self) -> ScopeId:
        return ScopeId(scope_type=ScopeType(self.owner_scope_type), scope_id=self.owner_scope_id)

    def entity_id(self) -> ObjectId:
        return ObjectId(entity_type=EntityType.VFOLDER, entity_id=self.parent_entity_id)

    def field_id(self) -> ObjectId:
        return ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(self.id))


# =============================================================================
# Tables List
# =============================================================================

PURGER_TABLES = [
    RBACPurgerTestRow,
    RBACPurgerFieldTestRow,
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
class FieldEntityContext:
    """Context for field-scoped entity."""

    field_uuid: UUID
    parent_entity_id: str
    user_id: str


@dataclass
class TwoFieldsContext:
    """Context with two fields for the same parent entity."""

    field_uuid1: UUID
    field_uuid2: UUID
    parent_entity_id: str
    user_id: str


@dataclass
class MultiScopeEntityContext:
    """Context with entity shared across multiple scopes."""

    entity_uuid: UUID
    owner_user_id: str
    shared_user_id: str


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC purger test tables."""
    async with with_tables(database_connection, PURGER_TABLES):
        yield


# =============================================================================
# Tests
# =============================================================================


class TestRBACPurgerBasic:
    """Basic tests for purger operations."""

    @pytest.fixture
    async def entity_with_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithAssociationContext, None]:
        """Create entity row and scope association."""
        user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()

        async with database_connection.begin_session() as db_sess:
            entity_row = RBACPurgerTestRow(
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

        async with database_connection.begin_session() as db_sess:
            purger: Purger[RBACPurgerTestRow] = Purger(
                row_class=RBACPurgerTestRow,
                pk_value=ctx.entity_uuid,
                entity_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(ctx.entity_uuid)),
                field_id=None,
            )
            result = await execute_purger(db_sess, purger)

            # Verify result
            assert isinstance(result, PurgerResult)
            assert result.row.id == ctx.entity_uuid
            assert result.row.name == "test-entity"

            # Verify main row deleted
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACPurgerTestRow)
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

        async with database_connection.begin_session() as db_sess:
            purger: Purger[RBACPurgerTestRow] = Purger(
                row_class=RBACPurgerTestRow,
                pk_value=nonexistent_uuid,
                entity_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(nonexistent_uuid)),
                field_id=None,
            )
            result = await execute_purger(db_sess, purger)
            assert result is None


class TestRBACPurgerWithObjectPermissions:
    """Tests for purger with object permissions cleanup."""

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

        async with database_connection.begin_session() as db_sess:
            entity_row = RBACPurgerTestRow(
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

        async with database_connection.begin_session() as db_sess:
            for entity_uuid, name in [(entity_uuid1, "entity-1"), (entity_uuid2, "entity-2")]:
                entity_row = RBACPurgerTestRow(
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

        async with database_connection.begin_session() as db_sess:
            purger: Purger[RBACPurgerTestRow] = Purger(
                row_class=RBACPurgerTestRow,
                pk_value=ctx.entity_uuid,
                entity_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(ctx.entity_uuid)),
                field_id=None,
            )
            await execute_purger(db_sess, purger)

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

        async with database_connection.begin_session() as db_sess:
            # Delete only entity1
            purger: Purger[RBACPurgerTestRow] = Purger(
                row_class=RBACPurgerTestRow,
                pk_value=ctx.entity_uuid1,
                entity_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(ctx.entity_uuid1)),
                field_id=None,
            )
            await execute_purger(db_sess, purger)

            # Verify only entity1's permissions deleted
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 1

            # Verify entity2's permission preserved
            remaining_perm = await db_sess.scalar(sa.select(ObjectPermissionRow))
            assert remaining_perm is not None
            assert remaining_perm.entity_id == str(ctx.entity_uuid2)


class TestRBACPurgerFieldScoped:
    """Tests for field-scoped entity purging."""

    @pytest.fixture
    async def field_entity(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[FieldEntityContext, None]:
        """Create field-scoped entity with EntityFieldRow."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())
        field_uuid = uuid.uuid4()

        async with database_connection.begin_session() as db_sess:
            field_row = RBACPurgerFieldTestRow(
                id=field_uuid,
                name="test-field",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
                parent_entity_id=parent_entity_id,
            )
            db_sess.add(field_row)

            entity_field = EntityFieldRow(
                entity_type=EntityType.VFOLDER.value,
                entity_id=parent_entity_id,
                field_type=EntityType.VFOLDER.value,
                field_id=str(field_uuid),
            )
            db_sess.add(entity_field)
            await db_sess.flush()

        yield FieldEntityContext(
            field_uuid=field_uuid,
            parent_entity_id=parent_entity_id,
            user_id=user_id,
        )

    @pytest.fixture
    async def two_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[TwoFieldsContext, None]:
        """Create two field entities for the same parent."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())
        field_uuid1 = uuid.uuid4()
        field_uuid2 = uuid.uuid4()

        async with database_connection.begin_session() as db_sess:
            for field_uuid, name in [(field_uuid1, "field-1"), (field_uuid2, "field-2")]:
                field_row = RBACPurgerFieldTestRow(
                    id=field_uuid,
                    name=name,
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                    parent_entity_id=parent_entity_id,
                )
                db_sess.add(field_row)

                entity_field = EntityFieldRow(
                    entity_type=EntityType.VFOLDER.value,
                    entity_id=parent_entity_id,
                    field_type=EntityType.VFOLDER.value,
                    field_id=str(field_uuid),
                )
                db_sess.add(entity_field)
            await db_sess.flush()

        yield TwoFieldsContext(
            field_uuid1=field_uuid1,
            field_uuid2=field_uuid2,
            parent_entity_id=parent_entity_id,
            user_id=user_id,
        )

    async def test_purger_deletes_entity_field_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        field_entity: FieldEntityContext,
    ) -> None:
        """Test that purger deletes EntityFieldRow for field-scoped entities."""
        ctx = field_entity

        async with database_connection.begin_session() as db_sess:
            purger: Purger[RBACPurgerFieldTestRow] = Purger(
                row_class=RBACPurgerFieldTestRow,
                pk_value=ctx.field_uuid,
                entity_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=ctx.parent_entity_id),
                field_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(ctx.field_uuid)),
            )
            result = await execute_purger(db_sess, purger)

            # Verify result
            assert isinstance(result, PurgerResult)
            assert result.row.id == ctx.field_uuid

            # Verify field entity row deleted
            field_entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACPurgerFieldTestRow)
            )
            assert field_entity_count == 0

            # Verify EntityFieldRow deleted
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_field_count == 0

    async def test_purger_field_preserves_other_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_fields: TwoFieldsContext,
    ) -> None:
        """Test that purging one field preserves other fields of the same entity."""
        ctx = two_fields

        async with database_connection.begin_session() as db_sess:
            # Delete only field1
            purger: Purger[RBACPurgerFieldTestRow] = Purger(
                row_class=RBACPurgerFieldTestRow,
                pk_value=ctx.field_uuid1,
                entity_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=ctx.parent_entity_id),
                field_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(ctx.field_uuid1)),
            )
            await execute_purger(db_sess, purger)

            # Verify only field1's EntityFieldRow deleted
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_field_count == 1

            # Verify field2 preserved
            remaining_field = await db_sess.scalar(sa.select(EntityFieldRow))
            assert remaining_field is not None
            assert remaining_field.field_id == str(ctx.field_uuid2)


class TestRBACPurgerPermissionGroupCleanup:
    """Tests for permission group cleanup during purging."""

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

        async with database_connection.begin_session() as db_sess:
            entity_row = RBACPurgerTestRow(
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

        async with database_connection.begin_session() as db_sess:
            for entity_uuid, name in [(entity_uuid1, "entity-1"), (entity_uuid2, "entity-2")]:
                entity_row = RBACPurgerTestRow(
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

        async with database_connection.begin_session() as db_sess:
            purger: Purger[RBACPurgerTestRow] = Purger(
                row_class=RBACPurgerTestRow,
                pk_value=ctx.entity_uuid,
                entity_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(ctx.entity_uuid)),
                field_id=None,
            )
            await execute_purger(db_sess, purger)

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

        async with database_connection.begin_session() as db_sess:
            # Delete entity1
            purger: Purger[RBACPurgerTestRow] = Purger(
                row_class=RBACPurgerTestRow,
                pk_value=ctx.entity_uuid1,
                entity_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(ctx.entity_uuid1)),
                field_id=None,
            )
            await execute_purger(db_sess, purger)

            # Verify permission group preserved (entity2 still has association in same scope)
            perm_group_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionGroupRow)
            )
            assert perm_group_count == 1


class TestRBACPurgerMultipleScopes:
    """Tests for purger with entities shared across multiple scopes."""

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

        async with database_connection.begin_session() as db_sess:
            entity_row = RBACPurgerTestRow(
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

        async with database_connection.begin_session() as db_sess:
            purger: Purger[RBACPurgerTestRow] = Purger(
                row_class=RBACPurgerTestRow,
                pk_value=ctx.entity_uuid,
                entity_id=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(ctx.entity_uuid)),
                field_id=None,
            )
            await execute_purger(db_sess, purger)

            # Verify all associations deleted
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0
