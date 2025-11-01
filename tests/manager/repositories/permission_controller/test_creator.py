"""
Tests for RBACEntityCreator and RBACCreator functionality.
Tests the creator classes with real database operations.
"""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.creator import (
    RBACCreator,
    RBACEntityCreator,
)


class ConcreteRBACEntityCreator(RBACEntityCreator):
    """Concrete implementation of RBACEntityCreator for testing."""

    def __init__(self, scope_id: ScopeId, object_id: ObjectId) -> None:
        self._scope_id = scope_id
        self._object_id = object_id

    def scope_id(self) -> ScopeId:
        return self._scope_id

    def object_id(self) -> ObjectId:
        return self._object_id


class ConcreteRBACCreator(RBACCreator[str]):
    """Concrete implementation of RBACCreator for testing."""

    def __init__(self, rbac_entity_creator: RBACEntityCreator, entity_value: str) -> None:
        super().__init__(rbac_entity_creator)
        self._entity_value = entity_value

    async def _create(self, db_session: SASession) -> str:
        return self._entity_value


class TestRBACEntityCreator:
    """Test cases for RBACEntityCreator"""

    @pytest.fixture
    async def test_scope_id(self) -> ScopeId:
        """Create a test scope ID"""
        return ScopeId(
            scope_type=ScopeType.DOMAIN,
            scope_id=f"test-domain-{uuid.uuid4().hex[:8]}",
        )

    @pytest.fixture
    async def test_object_id(self) -> ObjectId:
        """Create a test object ID"""
        return ObjectId(
            entity_type=EntityType.USER,
            entity_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    async def entity_creator(
        self,
        test_scope_id: ScopeId,
        test_object_id: ObjectId,
    ) -> ConcreteRBACEntityCreator:
        """Create a concrete RBAC entity creator for testing"""
        return ConcreteRBACEntityCreator(
            scope_id=test_scope_id,
            object_id=test_object_id,
        )

    @pytest.mark.asyncio
    async def test_create_entity_success(
        self,
        database_engine: ExtendedAsyncSAEngine,
        entity_creator: ConcreteRBACEntityCreator,
        test_scope_id: ScopeId,
        test_object_id: ObjectId,
    ) -> None:
        """Test creating entity association successfully"""
        async with database_engine.begin_session() as db_sess:
            await entity_creator.create_entity(db_sess)
            await db_sess.flush()

            # Verify the association was created
            result = await db_sess.execute(
                sa.select(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.scope_type == test_scope_id.scope_type,
                    AssociationScopesEntitiesRow.scope_id == test_scope_id.scope_id,
                    AssociationScopesEntitiesRow.entity_type == test_object_id.entity_type,
                    AssociationScopesEntitiesRow.entity_id == test_object_id.entity_id,
                )
            )
            association = result.scalar_one_or_none()

            assert association is not None
            assert association.scope_type == test_scope_id.scope_type
            assert association.scope_id == test_scope_id.scope_id
            assert association.entity_type == test_object_id.entity_type
            assert association.entity_id == test_object_id.entity_id

            # Cleanup
            await db_sess.execute(
                sa.delete(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.id == association.id
                )
            )

    @pytest.mark.asyncio
    async def test_create_entity_duplicate(
        self,
        database_engine: ExtendedAsyncSAEngine,
        entity_creator: ConcreteRBACEntityCreator,
        test_scope_id: ScopeId,
        test_object_id: ObjectId,
    ) -> None:
        """Test creating duplicate entity association in separate sessions"""
        # Create first association in one session
        async with database_engine.begin_session() as db_sess:
            await entity_creator.create_entity(db_sess)
            await db_sess.flush()

        # Try to create duplicate in a new session - should handle gracefully via IntegrityError catch
        async with database_engine.begin_session() as db_sess:
            await entity_creator.create_entity(db_sess)
            # No flush needed here as the IntegrityError is caught and logged

        # Verify only one association exists in a separate read session
        async with database_engine.begin_readonly_session() as db_sess:
            result = await db_sess.execute(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(
                    AssociationScopesEntitiesRow.scope_type == test_scope_id.scope_type,
                    AssociationScopesEntitiesRow.scope_id == test_scope_id.scope_id,
                    AssociationScopesEntitiesRow.entity_type == test_object_id.entity_type,
                    AssociationScopesEntitiesRow.entity_id == test_object_id.entity_id,
                )
            )
            count = result.scalar()
            assert count == 1

        # Cleanup in final session
        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(
                sa.delete(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.scope_type == test_scope_id.scope_type,
                    AssociationScopesEntitiesRow.scope_id == test_scope_id.scope_id,
                    AssociationScopesEntitiesRow.entity_type == test_object_id.entity_type,
                    AssociationScopesEntitiesRow.entity_id == test_object_id.entity_id,
                )
            )

    @pytest.mark.asyncio
    async def test_scope_id_and_object_id_methods(
        self,
        entity_creator: ConcreteRBACEntityCreator,
        test_scope_id: ScopeId,
        test_object_id: ObjectId,
    ) -> None:
        """Test scope_id and object_id methods return correct values"""
        assert entity_creator.scope_id() == test_scope_id
        assert entity_creator.object_id() == test_object_id


class TestRBACCreator:
    """Test cases for RBACCreator"""

    @pytest.fixture
    async def test_scope_id(self) -> ScopeId:
        """Create a test scope ID"""
        return ScopeId(
            scope_type=ScopeType.PROJECT,
            scope_id=f"test-project-{uuid.uuid4().hex[:8]}",
        )

    @pytest.fixture
    async def test_object_id(self) -> ObjectId:
        """Create a test object ID"""
        return ObjectId(
            entity_type=EntityType.VFOLDER,
            entity_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    async def entity_creator(
        self,
        test_scope_id: ScopeId,
        test_object_id: ObjectId,
    ) -> ConcreteRBACEntityCreator:
        """Create a concrete RBAC entity creator for testing"""
        return ConcreteRBACEntityCreator(
            scope_id=test_scope_id,
            object_id=test_object_id,
        )

    @pytest.fixture
    async def rbac_creator(
        self,
        entity_creator: ConcreteRBACEntityCreator,
    ) -> ConcreteRBACCreator:
        """Create a concrete RBAC creator for testing"""
        return ConcreteRBACCreator(
            rbac_entity_creator=entity_creator,
            entity_value="test-entity-value",
        )

    @pytest.mark.asyncio
    async def test_create_with_entity_association(
        self,
        database_engine: ExtendedAsyncSAEngine,
        rbac_creator: ConcreteRBACCreator,
        test_scope_id: ScopeId,
        test_object_id: ObjectId,
    ) -> None:
        """Test creating entity with RBAC association"""
        async with database_engine.begin_session() as db_sess:
            result = await rbac_creator.create(db_sess)
            await db_sess.flush()

            # Verify the entity was created
            assert result == "test-entity-value"

            # Verify the association was created
            association_result = await db_sess.execute(
                sa.select(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.scope_type == test_scope_id.scope_type,
                    AssociationScopesEntitiesRow.scope_id == test_scope_id.scope_id,
                    AssociationScopesEntitiesRow.entity_type == test_object_id.entity_type,
                    AssociationScopesEntitiesRow.entity_id == test_object_id.entity_id,
                )
            )
            association = association_result.scalar_one_or_none()

            assert association is not None
            assert association.scope_type == test_scope_id.scope_type
            assert association.scope_id == test_scope_id.scope_id
            assert association.entity_type == test_object_id.entity_type
            assert association.entity_id == test_object_id.entity_id

            # Cleanup
            await db_sess.execute(
                sa.delete(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.id == association.id
                )
            )
