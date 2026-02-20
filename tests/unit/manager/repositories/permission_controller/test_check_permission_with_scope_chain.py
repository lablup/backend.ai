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
        async with db_with_rbac_tables.begin_session() as db_sess:
            assoc = AssociationScopesEntitiesRow(
                scope_type=ScopeType.PROJECT,
                scope_id=fixture_ids.project_id,
                entity_type=EntityType.VFOLDER,
                entity_id=fixture_ids.vfolder_id,
                relation_type=RelationType.AUTO,
            )
            db_sess.add(assoc)
            await db_sess.flush()

    @pytest.fixture
    async def project_in_domain_auto(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> None:
        """PROJECT belongs to DOMAIN (auto edge)."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            assoc = AssociationScopesEntitiesRow(
                scope_type=ScopeType.DOMAIN,
                scope_id=fixture_ids.domain_id,
                entity_type=EntityType.PROJECT,
                entity_id=fixture_ids.project_id,
                relation_type=RelationType.AUTO,
            )
            db_sess.add(assoc)
            await db_sess.flush()

    @pytest.fixture
    async def vfolder_in_project_ref(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> None:
        """VFOLDER referenced by PROJECT (ref edge)."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            assoc = AssociationScopesEntitiesRow(
                scope_type=ScopeType.PROJECT,
                scope_id=fixture_ids.project_id,
                entity_type=EntityType.VFOLDER,
                entity_id=fixture_ids.vfolder_id,
                relation_type=RelationType.REF,
            )
            db_sess.add(assoc)
            await db_sess.flush()

    @pytest.fixture
    async def permission_setup(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
        request: pytest.FixtureRequest,
    ) -> None:
        scope_map: dict[str, tuple[ScopeType, str]] = {
            "project": (ScopeType.PROJECT, fixture_ids.project_id),
            "domain": (ScopeType.DOMAIN, fixture_ids.domain_id),
        }
        for scope_key, operation in request.param:
            scope_type, scope_id = scope_map[scope_key]
            async with db_with_rbac_tables.begin_session() as db_sess:
                perm = PermissionRow(
                    role_id=fixture_ids.role_id,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    entity_type=EntityType.VFOLDER,
                    operation=operation,
                )
                db_sess.add(perm)
                await db_sess.flush()

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param([], OperationType.READ, False, id="no-permission"),
            pytest.param(
                [("project", OperationType.READ)],
                OperationType.READ,
                True,
                id="direct-scope-read",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_vfolder_auto_in_project(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """VFOLDER in PROJECT (auto): direct scope permission checks."""
        f = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [("domain", OperationType.UPDATE)],
                OperationType.UPDATE,
                True,
                id="parent-scope-update",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_vfolder_auto_chain_to_domain(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        project_in_domain_auto: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """AUTO edge delegates all operations from parent scope."""
        f = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [("project", OperationType.READ)],
                OperationType.READ,
                False,
                id="ref-blocks-read",
            ),
            pytest.param(
                [("project", OperationType.UPDATE)],
                OperationType.UPDATE,
                False,
                id="ref-blocks-update",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_vfolder_ref_in_project(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_ref: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """REF edge is not traversed; no operation passes through."""
        f = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [("domain", OperationType.READ)],
                OperationType.READ,
                False,
                id="ref-stops-chain",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_vfolder_ref_chain_to_domain(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_ref: None,
        project_in_domain_auto: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """REF edge terminates scope chain; scopes beyond REF are unreachable."""
        f = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    @pytest.fixture
    async def user_with_inactive_role(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> ScopeChainFixture:
        """Create a user with an inactive role."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            role = RoleRow(
                id=fixture_ids.role_id,
                name="inactive-role",
                status=RoleStatus.INACTIVE,
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

    @pytest.mark.parametrize(
        ("permission_setup",),
        [
            pytest.param([("project", OperationType.READ)], id="inactive-role-read"),
        ],
        indirect=["permission_setup"],
    )
    async def test_inactive_role_denied(
        self,
        db_source: PermissionDBSource,
        user_with_inactive_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        """Inactive role does not grant any permission."""
        f = user_with_inactive_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=f.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=f.vfolder_id,
            ),
            operation=OperationType.READ,
        )
        assert result is False
