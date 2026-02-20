"""
Tests for PermissionDBSource.check_permission_with_scope_chain().
Covers CTE-based scope chain traversal with AUTO/REF edge semantics and GLOBAL fallback.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import pytest

from ai.backend.common.data.permission.types import (
    RBACElementType,
    RelationType,
)
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RBACElementRef,
    ScopeType,
)
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables


@dataclass
class ScopeChainFixture:
    """Pre-built fixture data for scope chain tests."""

    user_id: uuid.UUID
    role_id: uuid.UUID
    domain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vfolder_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class TestCheckPermissionWithScopeChain:
    """Tests for CTE-based scope chain permission traversal."""

    @pytest.fixture
    async def db_with_rbac_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                RoleRow,
                UserRoleRow,
                PermissionRow,
                ObjectPermissionRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def db_source(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionDBSource:
        return PermissionDBSource(db_with_rbac_tables)

    @pytest.fixture
    def fixture_ids(self) -> ScopeChainFixture:
        return ScopeChainFixture(
            user_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
        )

    @pytest.fixture
    async def user_with_active_role(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> ScopeChainFixture:
        """Create a user with an active role (no permissions yet)."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            role = RoleRow(
                id=fixture_ids.role_id,
                name="test-role",
                description="Test role for scope chain",
            )
            db_sess.add(role)
            await db_sess.flush()

            user_role = UserRoleRow(
                user_id=fixture_ids.user_id,
                role_id=fixture_ids.role_id,
            )
            db_sess.add(user_role)
            await db_sess.flush()

        return fixture_ids

    @pytest.fixture
    async def vfolder_in_project_auto(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> None:
        """VFOLDER belongs to PROJECT (auto edge)."""
        await self._add_association(
            db_with_rbac_tables,
            scope_type=ScopeType.PROJECT,
            scope_id=fixture_ids.project_id,
            entity_type=EntityType.VFOLDER,
            entity_id=fixture_ids.vfolder_id,
        )

    @pytest.fixture
    async def project_in_domain_auto(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> None:
        """PROJECT belongs to DOMAIN (auto edge)."""
        await self._add_association(
            db_with_rbac_tables,
            scope_type=ScopeType.DOMAIN,
            scope_id=fixture_ids.domain_id,
            entity_type=EntityType.PROJECT,
            entity_id=fixture_ids.project_id,
        )

    @pytest.fixture
    async def vfolder_in_project_ref(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> None:
        """VFOLDER referenced by PROJECT (ref edge)."""
        await self._add_association(
            db_with_rbac_tables,
            scope_type=ScopeType.PROJECT,
            scope_id=fixture_ids.project_id,
            entity_type=EntityType.VFOLDER,
            entity_id=fixture_ids.vfolder_id,
            relation_type=RelationType.REF,
        )

    async def _add_permission(
        self,
        db: ExtendedAsyncSAEngine,
        role_id: uuid.UUID,
        scope_type: ScopeType,
        scope_id: str,
        entity_type: EntityType,
        operation: OperationType,
    ) -> None:
        async with db.begin_session() as db_sess:
            perm = PermissionRow(
                role_id=role_id,
                scope_type=scope_type,
                scope_id=scope_id,
                entity_type=entity_type,
                operation=operation,
            )
            db_sess.add(perm)
            await db_sess.flush()

    async def _add_association(
        self,
        db: ExtendedAsyncSAEngine,
        scope_type: ScopeType,
        scope_id: str,
        entity_type: EntityType,
        entity_id: str,
        relation_type: RelationType = RelationType.AUTO,
    ) -> None:
        async with db.begin_session() as db_sess:
            assoc = AssociationScopesEntitiesRow(
                scope_type=scope_type,
                scope_id=scope_id,
                entity_type=entity_type,
                entity_id=entity_id,
                relation_type=relation_type,
            )
            db_sess.add(assoc)
            await db_sess.flush()

    async def test_direct_scope_match(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
    ) -> None:
        """Permission on the direct scope of the target entity grants access."""
        f = user_with_active_role

        # User has READ permission on VFOLDER in that PROJECT scope
        await self._add_permission(
            db_with_rbac_tables,
            role_id=f.role_id,
            scope_type=ScopeType.PROJECT,
            scope_id=f.project_id,
            entity_type=EntityType.VFOLDER,
            operation=OperationType.READ,
        )

        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=OperationType.READ,
        )
        assert result is True

    async def test_no_permission_returns_false(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
    ) -> None:
        """No matching permission anywhere in the chain returns False."""
        f = user_with_active_role

        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=OperationType.READ,
        )
        assert result is False

    async def test_auto_delegation_from_parent_scope(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        project_in_domain_auto: None,
    ) -> None:
        """AUTO edge delegates all operations from parent scope."""
        f = user_with_active_role

        # Permission granted at DOMAIN scope
        await self._add_permission(
            db_with_rbac_tables,
            role_id=f.role_id,
            scope_type=ScopeType.DOMAIN,
            scope_id=f.domain_id,
            entity_type=EntityType.VFOLDER,
            operation=OperationType.UPDATE,
        )

        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=OperationType.UPDATE,
        )
        assert result is True

    async def test_ref_edge_blocks_all_operations(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_ref: None,
    ) -> None:
        """REF edge is not traversed; no operation passes through."""
        f = user_with_active_role

        await self._add_permission(
            db_with_rbac_tables,
            role_id=f.role_id,
            scope_type=ScopeType.PROJECT,
            scope_id=f.project_id,
            entity_type=EntityType.VFOLDER,
            operation=OperationType.READ,
        )
        await self._add_permission(
            db_with_rbac_tables,
            role_id=f.role_id,
            scope_type=ScopeType.PROJECT,
            scope_id=f.project_id,
            entity_type=EntityType.VFOLDER,
            operation=OperationType.UPDATE,
        )

        # READ blocked — ref edge is not part of scope chain
        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=OperationType.READ,
        )
        assert result is False

        # CUD also blocked
        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=OperationType.UPDATE,
        )
        assert result is False

    async def test_ref_edge_stops_chaining(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_ref: None,
        project_in_domain_auto: None,
    ) -> None:
        """REF edge terminates scope chain; scopes beyond REF are unreachable."""
        f = user_with_active_role

        # Permission at DOMAIN scope — beyond the REF edge
        await self._add_permission(
            db_with_rbac_tables,
            role_id=f.role_id,
            scope_type=ScopeType.DOMAIN,
            scope_id=f.domain_id,
            entity_type=EntityType.VFOLDER,
            operation=OperationType.READ,
        )

        # Chain stops at REF; DOMAIN scope is unreachable
        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=OperationType.READ,
        )
        assert result is False

    async def test_inactive_role_denied(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        fixture_ids: ScopeChainFixture,
        vfolder_in_project_auto: None,
    ) -> None:
        """Inactive role does not grant any permission."""
        f = fixture_ids

        async with db_with_rbac_tables.begin_session() as db_sess:
            role = RoleRow(
                id=f.role_id,
                name="inactive-role",
                status=RoleStatus.INACTIVE,
            )
            db_sess.add(role)
            await db_sess.flush()

            user_role = UserRoleRow(
                user_id=f.user_id,
                role_id=f.role_id,
            )
            db_sess.add(user_role)
            await db_sess.flush()

        await self._add_permission(
            db_with_rbac_tables,
            role_id=f.role_id,
            scope_type=ScopeType.PROJECT,
            scope_id=f.project_id,
            entity_type=EntityType.VFOLDER,
            operation=OperationType.READ,
        )

        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=OperationType.READ,
        )
        assert result is False
