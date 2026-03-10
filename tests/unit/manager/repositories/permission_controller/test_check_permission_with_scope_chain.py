"""
Tests for PermissionDBSource.check_permission_with_scope_chain().
Covers CTE-based scope chain traversal with AUTO/REF edge semantics.
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
class PermissionEntry:
    """A single permission to create in permission_setup fixture."""

    scope_key: str
    operation: OperationType
    entity_type: EntityType = EntityType.VFOLDER


@dataclass
class ScopeChainFixture:
    """Pre-built fixture data for scope chain tests."""

    user_id: uuid.UUID
    role_id: uuid.UUID
    domain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vfolder_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_scope_id: str = field(default_factory=lambda: str(uuid.uuid4()))


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
            "vfolder": (ScopeType.VFOLDER, fixture_ids.vfolder_id),
            "project": (ScopeType.PROJECT, fixture_ids.project_id),
            "domain": (ScopeType.DOMAIN, fixture_ids.domain_id),
            "user_scope": (ScopeType.USER, fixture_ids.user_scope_id),
        }
        for entry in request.param:
            if not isinstance(entry, PermissionEntry):
                raise TypeError(f"Expected PermissionEntry, got {type(entry).__name__}: {entry!r}")
            scope_type, scope_id = scope_map[entry.scope_key]
            async with db_with_rbac_tables.begin_session() as db_sess:
                perm = PermissionRow(
                    role_id=fixture_ids.role_id,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    entity_type=entry.entity_type,
                    operation=entry.operation,
                )
                db_sess.add(perm)
                await db_sess.flush()

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param([], OperationType.READ, False, id="no-permission"),
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
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
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.UPDATE)],
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
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
                OperationType.READ,
                False,
                id="ref-blocks-read",
            ),
            pytest.param(
                [PermissionEntry("project", OperationType.UPDATE)],
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
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.READ)],
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
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
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
            pytest.param([PermissionEntry("project", OperationType.READ)], id="inactive-role-read"),
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
        fixture = user_with_inactive_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=OperationType.READ,
        )
        assert result is False

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("vfolder", OperationType.READ)],
                OperationType.READ,
                True,
                id="self-scope-read",
            ),
            pytest.param(
                [PermissionEntry("vfolder", OperationType.UPDATE)],
                OperationType.UPDATE,
                True,
                id="self-scope-update",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_self_scope_permission(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_ref: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """Permission scoped directly to the target entity itself is honored."""
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("vfolder", OperationType.READ)],
                OperationType.READ,
                True,
                id="self-scope-no-assoc",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_self_scope_without_any_association(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """Self-scope permission works even without any association edges."""
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    # ── A. Operation mismatch ──

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
                OperationType.UPDATE,
                False,
                id="project-read-perm-check-update",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_operation_mismatch_direct_scope(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """Permission exists but for a different operation; check should fail."""
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.CREATE)],
                OperationType.SOFT_DELETE,
                False,
                id="domain-create-perm-check-soft-delete",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_operation_mismatch_chain_scope(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        project_in_domain_auto: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """Operation mismatch at chain-traversed scope still returns False."""
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    # ── B. DELETED role ──

    @pytest.fixture
    async def user_with_deleted_role(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> ScopeChainFixture:
        """Create a user with a deleted role."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            role = RoleRow(
                id=fixture_ids.role_id,
                name="deleted-role",
                status=RoleStatus.DELETED,
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
            pytest.param([PermissionEntry("project", OperationType.READ)], id="deleted-role-read"),
        ],
        indirect=["permission_setup"],
    )
    async def test_deleted_role_denied(
        self,
        db_source: PermissionDBSource,
        user_with_deleted_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        """Deleted role does not grant any permission."""
        fixture = user_with_deleted_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=OperationType.READ,
        )
        assert result is False

    # ── C. No role assigned ──

    @pytest.fixture
    async def user_with_unassigned_role(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> ScopeChainFixture:
        """Create a role with permission but do NOT assign it to the user."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            role = RoleRow(
                id=fixture_ids.role_id,
                name="unassigned-role",
            )
            db_sess.add(role)
            await db_sess.flush()

            perm = PermissionRow(
                role_id=fixture_ids.role_id,
                scope_type=ScopeType.PROJECT,
                scope_id=fixture_ids.project_id,
                entity_type=EntityType.VFOLDER,
                operation=OperationType.READ,
            )
            db_sess.add(perm)
            await db_sess.flush()

        return fixture_ids

    async def test_no_role_assigned(
        self,
        db_source: PermissionDBSource,
        user_with_unassigned_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
    ) -> None:
        """User with no role assignment gets no permission."""
        fixture = user_with_unassigned_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=OperationType.READ,
        )
        assert result is False

    # ── D. Multiple roles ──

    @pytest.fixture
    async def user_with_two_roles(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> tuple[ScopeChainFixture, uuid.UUID]:
        """Create a user with two active roles. Returns (fixture, second_role_id)."""
        second_role_id = uuid.uuid4()
        async with db_with_rbac_tables.begin_session() as db_sess:
            role1 = RoleRow(
                id=fixture_ids.role_id,
                name="role-1",
            )
            role2 = RoleRow(
                id=second_role_id,
                name="role-2",
            )
            db_sess.add_all([role1, role2])
            await db_sess.flush()

            ur1 = UserRoleRow(
                user_id=fixture_ids.user_id,
                role_id=fixture_ids.role_id,
            )
            ur2 = UserRoleRow(
                user_id=fixture_ids.user_id,
                role_id=second_role_id,
            )
            db_sess.add_all([ur1, ur2])
            await db_sess.flush()

        return fixture_ids, second_role_id

    @pytest.fixture
    async def multi_role_permission_setup(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
        user_with_two_roles: tuple[ScopeChainFixture, uuid.UUID],
        request: pytest.FixtureRequest,
    ) -> None:
        """Set up permissions for multi-role tests. Each entry: (role_key, scope_key, operation)."""
        _, second_role_id = user_with_two_roles
        role_map: dict[str, uuid.UUID] = {
            "first": fixture_ids.role_id,
            "second": second_role_id,
        }
        scope_map: dict[str, tuple[ScopeType, str]] = {
            "project": (ScopeType.PROJECT, fixture_ids.project_id),
            "domain": (ScopeType.DOMAIN, fixture_ids.domain_id),
        }
        for role_key, scope_key, operation in request.param:
            role_id = role_map[role_key]
            scope_type, scope_id = scope_map[scope_key]
            async with db_with_rbac_tables.begin_session() as db_sess:
                perm = PermissionRow(
                    role_id=role_id,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    entity_type=EntityType.VFOLDER,
                    operation=operation,
                )
                db_sess.add(perm)
                await db_sess.flush()

    @pytest.mark.parametrize(
        ("multi_role_permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [("second", "project", OperationType.READ)],
                OperationType.READ,
                True,
                id="one-role-has-read",
            ),
            pytest.param(
                [
                    ("first", "project", OperationType.READ),
                    ("second", "project", OperationType.READ),
                ],
                OperationType.UPDATE,
                False,
                id="both-roles-read-check-update",
            ),
        ],
        indirect=["multi_role_permission_setup"],
    )
    async def test_multiple_roles(
        self,
        db_source: PermissionDBSource,
        user_with_two_roles: tuple[ScopeChainFixture, uuid.UUID],
        vfolder_in_project_auto: None,
        multi_role_permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """Multiple roles: succeeds if any role matches, fails if none does."""
        fixture, _ = user_with_two_roles
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    # ── E. Mixed edge chain (AUTO→REF, REF→AUTO) ──

    @pytest.fixture
    async def project_in_domain_ref(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> None:
        """PROJECT referenced by DOMAIN (ref edge)."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            assoc = AssociationScopesEntitiesRow(
                scope_type=ScopeType.DOMAIN,
                scope_id=fixture_ids.domain_id,
                entity_type=EntityType.PROJECT,
                entity_id=fixture_ids.project_id,
                relation_type=RelationType.REF,
            )
            db_sess.add(assoc)
            await db_sess.flush()

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.READ)],
                OperationType.READ,
                False,
                id="auto-then-ref-blocks-domain",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_auto_then_ref_blocks_chain(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        project_in_domain_ref: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """VFOLDER→(AUTO)→PROJECT→(REF)→DOMAIN: REF in the middle blocks chain."""
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
                OperationType.READ,
                True,
                id="auto-segment-before-ref-valid",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_auto_segment_before_ref_valid(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        project_in_domain_ref: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """VFOLDER→(AUTO)→PROJECT→(REF)→DOMAIN: PROJECT scope is still reachable."""
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    # ── F. Deep chain (3-level AUTO) ──

    @pytest.fixture
    async def domain_in_user_scope_auto(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> None:
        """DOMAIN belongs to USER scope (auto edge) — 3rd level."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            assoc = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=fixture_ids.user_scope_id,
                entity_type=EntityType.DOMAIN,
                entity_id=fixture_ids.domain_id,
                relation_type=RelationType.AUTO,
            )
            db_sess.add(assoc)
            await db_sess.flush()

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("user_scope", OperationType.READ)],
                OperationType.READ,
                True,
                id="three-level-auto-chain",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_deep_three_level_auto_chain(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        project_in_domain_auto: None,
        domain_in_user_scope_auto: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """VFOLDER→(AUTO)→PROJECT→(AUTO)→DOMAIN→(AUTO)→USER: 3-level chain traversal."""
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    # ── G. Self-scope + AUTO edge combination ──

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("vfolder", OperationType.READ)],
                OperationType.READ,
                True,
                id="self-scope-with-auto-edge",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_self_scope_with_auto_edge(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """Self-scope permission works regardless of AUTO edge presence."""
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    # ── H. User isolation ──

    @pytest.fixture
    async def other_user_with_permission(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: ScopeChainFixture,
    ) -> None:
        """Create another user with a role and READ permission on the same project."""
        other_user_id = uuid.uuid4()
        other_role_id = uuid.uuid4()

        async with db_with_rbac_tables.begin_session() as db_sess:
            role = RoleRow(
                id=other_role_id,
                name="other-user-role",
            )
            db_sess.add(role)
            await db_sess.flush()

            user_role = UserRoleRow(
                user_id=other_user_id,
                role_id=other_role_id,
            )
            db_sess.add(user_role)
            await db_sess.flush()

            perm = PermissionRow(
                role_id=other_role_id,
                scope_type=ScopeType.PROJECT,
                scope_id=fixture_ids.project_id,
                entity_type=EntityType.VFOLDER,
                operation=OperationType.READ,
            )
            db_sess.add(perm)
            await db_sess.flush()

    async def test_other_user_permission_isolation(
        self,
        db_source: PermissionDBSource,
        fixture_ids: ScopeChainFixture,
        vfolder_in_project_auto: None,
        other_user_with_permission: None,
    ) -> None:
        """Permission granted to another user does not affect the target user."""
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture_ids.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture_ids.vfolder_id,
            ),
            operation=OperationType.READ,
        )
        assert result is False

    # ── I. Multiple permissions on same role ──

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [
                    PermissionEntry("project", OperationType.READ),
                    PermissionEntry("project", OperationType.UPDATE),
                ],
                OperationType.READ,
                True,
                id="multi-perm-read-matches",
            ),
            pytest.param(
                [
                    PermissionEntry("project", OperationType.READ),
                    PermissionEntry("project", OperationType.UPDATE),
                ],
                OperationType.SOFT_DELETE,
                False,
                id="multi-perm-soft-delete-no-match",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_multiple_permissions_on_same_role(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """Role with READ+UPDATE: READ matches, SOFT_DELETE does not."""
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected

    # ── J. Different entity_type permission ──

    @pytest.mark.parametrize(
        ("permission_setup", "check_op", "expected"),
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ, EntityType.SESSION)],
                OperationType.READ,
                False,
                id="session-perm-vfolder-check",
            ),
        ],
        indirect=["permission_setup"],
    )
    async def test_entity_type_mismatch(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: ScopeChainFixture,
        vfolder_in_project_auto: None,
        permission_setup: None,
        check_op: OperationType,
        expected: bool,
    ) -> None:
        """SESSION entity permission does not match VFOLDER entity check."""
        fixture = user_with_active_role
        result = await db_source.check_permission_with_scope_chain(
            user_id=fixture.user_id,
            target_element_ref=RBACElementRef(
                element_type=RBACElementType.VFOLDER,
                element_id=fixture.vfolder_id,
            ),
            operation=check_op,
        )
        assert result is expected
