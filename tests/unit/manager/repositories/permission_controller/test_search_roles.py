"""
Tests for PermissionControllerRepository.search_roles() functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
)
from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RBACElementType,
    ScopeType,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.agent import AgentRow

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.conditions import (
    AssignedUserConditions,
    EntityScopeConditions,
    RoleConditions,
)
from ai.backend.manager.models.rbac_models.orders import RoleOrders
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    CursorForwardPagination,
    OffsetPagination,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentRow,
    ScalingGroupForDomainRow,
    ImageRow,
)


@dataclass
class CreatedRole:
    role_id: uuid.UUID
    role_name: str
    created_at: datetime


class TestSearchRoles:
    """Tests for searching roles with filtering and ordering."""

    @pytest.fixture
    async def db_with_rbac_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                PermissionRow,
                ObjectPermissionRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        return PermissionControllerRepository(db_with_rbac_tables)

    @pytest.fixture
    async def created_roles(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> list[CreatedRole]:
        """Create multiple roles for testing."""
        created: list[CreatedRole] = []
        base_time = datetime(2026, 1, 1, tzinfo=UTC)

        async with db_with_rbac_tables.begin_session() as db_sess:
            for i, (name, description) in enumerate([
                ("admin-role", "Admin role"),
                ("editor-role", "Editor role"),
                ("viewer-role", "Viewer role"),
            ]):
                created_at = base_time + timedelta(minutes=i)
                role = RoleRow(
                    name=name,
                    description=description,
                    created_at=created_at,
                )
                db_sess.add(role)
                await db_sess.flush()
                created.append(
                    CreatedRole(
                        role_id=role.id,
                        role_name=name,
                        created_at=role.created_at,
                    )
                )

        return created

    async def test_search_roles_with_name_filter(
        self,
        repository: PermissionControllerRepository,
        created_roles: list[CreatedRole],
    ) -> None:
        """Name ends-with filter should match all roles ending with '-role'."""
        querier = BatchQuerier(
            conditions=[
                RoleConditions.by_name_ends_with(
                    StringMatchSpec(value="-role", case_insensitive=False, negated=False)
                ),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        assert result.total_count == len(created_roles)

    async def test_search_roles_ordered_by_name(
        self,
        repository: PermissionControllerRepository,
        created_roles: list[CreatedRole],
    ) -> None:
        querier = BatchQuerier(
            conditions=[],
            orders=[RoleOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        names = [item.name for item in result.items]
        expected_names = sorted([r.role_name for r in created_roles])
        assert names == expected_names

    async def test_search_roles_ordered_by_created_at(
        self,
        repository: PermissionControllerRepository,
        created_roles: list[CreatedRole],
    ) -> None:
        """Roles created sequentially should be ordered by created_at."""
        querier = BatchQuerier(
            conditions=[],
            orders=[RoleOrders.created_at(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        role_ids = [item.id for item in result.items]
        expected_role_ids = [r.role_id for r in sorted(created_roles, key=lambda r: r.created_at)]
        assert role_ids == expected_role_ids, (
            f"Failed to order roles by created_at: got {[r.created_at for r in result.items]}, expected {[r.created_at for r in created_roles]}"
        )

    @pytest.fixture
    async def roles_assigned_to_users(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        created_roles: list[CreatedRole],
    ) -> tuple[uuid.UUID, uuid.UUID, list[CreatedRole]]:
        """Create two users and assign the first role to the first user only.

        Returns ``(assigned_user_id, unassigned_user_id, created_roles)``.
        """
        assigned_user_id = uuid.uuid4()
        unassigned_user_id = uuid.uuid4()

        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="domain for by_assigned_user_id test",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=0,
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            await db_sess.flush()

            for user_id, suffix in [
                (assigned_user_id, "assigned"),
                (unassigned_user_id, "unassigned"),
            ]:
                db_sess.add(
                    UserRow(
                        uuid=user_id,
                        username=f"{suffix}-{user_id.hex[:8]}",
                        email=f"{suffix}-{user_id.hex[:8]}@example.com",
                        password=password_info,
                        need_password_change=False,
                        status=UserStatus.ACTIVE,
                        status_info="active",
                        domain_name=domain_name,
                        role=UserRole.USER,
                        resource_policy=policy_name,
                    )
                )
            await db_sess.flush()

            db_sess.add(
                UserRoleRow(
                    user_id=assigned_user_id,
                    role_id=created_roles[0].role_id,
                )
            )
            await db_sess.flush()

        return assigned_user_id, unassigned_user_id, created_roles

    async def test_by_assigned_user_id_returns_only_assigned_roles(
        self,
        repository: PermissionControllerRepository,
        roles_assigned_to_users: tuple[uuid.UUID, uuid.UUID, list[CreatedRole]],
    ) -> None:
        """``RoleConditions.by_assigned_user_id`` should restrict results
        to roles assigned to the given user via the correlated EXISTS subquery."""
        assigned_user_id, _, created_roles = roles_assigned_to_users

        querier = BatchQuerier(
            conditions=[
                RoleConditions.by_assigned_user_id([
                    AssignedUserConditions.by_user_id_equals(
                        UUIDEqualMatchSpec(value=assigned_user_id, negated=False)
                    )
                ]),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        assert result.total_count == 1
        assert [item.id for item in result.items] == [created_roles[0].role_id]

    async def test_by_assigned_user_id_returns_empty_for_unassigned_user(
        self,
        repository: PermissionControllerRepository,
        roles_assigned_to_users: tuple[uuid.UUID, uuid.UUID, list[CreatedRole]],
    ) -> None:
        """A user with no assignments should yield no roles."""
        _, unassigned_user_id, _ = roles_assigned_to_users

        querier = BatchQuerier(
            conditions=[
                RoleConditions.by_assigned_user_id([
                    AssignedUserConditions.by_user_id_equals(
                        UUIDEqualMatchSpec(value=unassigned_user_id, negated=False)
                    )
                ]),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        assert result.total_count == 0
        assert result.items == []

    @pytest.fixture
    async def roles_mapped_to_scope(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        created_roles: list[CreatedRole],
    ) -> tuple[str, list[CreatedRole]]:
        """Map the first role to a project scope via ``association_scopes_entities``.

        Returns ``(project_scope_id, created_roles)``.
        """
        project_scope_id = str(uuid.uuid4())

        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=project_scope_id,
                    entity_type=EntityType.ROLE,
                    entity_id=str(created_roles[0].role_id),
                )
            )
            await db_sess.flush()

        return project_scope_id, created_roles

    async def test_by_mapped_scope_returns_roles_in_scope(
        self,
        repository: PermissionControllerRepository,
        roles_mapped_to_scope: tuple[str, list[CreatedRole]],
    ) -> None:
        """``RoleConditions.by_mapped_scope`` should restrict results to roles
        registered in the given scope via the correlated EXISTS subquery."""
        project_scope_id, created_roles = roles_mapped_to_scope

        querier = BatchQuerier(
            conditions=[
                RoleConditions.by_mapped_scope([
                    EntityScopeConditions.by_scope_type_equals(RBACElementType.PROJECT),
                    EntityScopeConditions.by_scope_id_equals(
                        StringMatchSpec(
                            value=project_scope_id, case_insensitive=False, negated=False
                        )
                    ),
                ]),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        assert result.total_count == 1
        assert [item.id for item in result.items] == [created_roles[0].role_id]


class TestSearchRolesTotalCountNotInflated:
    """Regression tests for BA-5749: total_count must not be inflated by ObjectPermissionRow JOIN."""

    @pytest.fixture
    async def db_with_rbac_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                PermissionRow,
                ObjectPermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        return PermissionControllerRepository(db_with_rbac_tables)

    @pytest.fixture
    async def roles_with_object_permissions(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> list[CreatedRole]:
        """Create 2 roles: one with 3 ObjectPermissionRows, one with 0."""
        created: list[CreatedRole] = []
        base_time = datetime(2026, 1, 1, tzinfo=UTC)

        async with db_with_rbac_tables.begin_session() as db_sess:
            # Role with multiple object permissions
            role_with_perms = RoleRow(
                name="role-with-perms",
                description="Role that has multiple object permissions",
                created_at=base_time,
            )
            db_sess.add(role_with_perms)
            await db_sess.flush()
            created.append(
                CreatedRole(
                    role_id=role_with_perms.id,
                    role_name="role-with-perms",
                    created_at=role_with_perms.created_at,
                )
            )

            # Add 3 ObjectPermissionRow entries for this role
            for op_type in [OperationType.READ, OperationType.UPDATE, OperationType.CREATE]:
                obj_perm = ObjectPermissionRow(
                    role_id=role_with_perms.id,
                    entity_type=EntityType.PROJECT,
                    entity_id=str(uuid.uuid4()),
                    operation=op_type,
                )
                db_sess.add(obj_perm)

            # Role with zero object permissions
            role_without_perms = RoleRow(
                name="role-without-perms",
                description="Role that has no object permissions",
                created_at=base_time + timedelta(minutes=1),
            )
            db_sess.add(role_without_perms)
            await db_sess.flush()
            created.append(
                CreatedRole(
                    role_id=role_without_perms.id,
                    role_name="role-without-perms",
                    created_at=role_without_perms.created_at,
                )
            )

        return created

    async def test_total_count_not_inflated_with_offset_pagination(
        self,
        repository: PermissionControllerRepository,
        roles_with_object_permissions: list[CreatedRole],
    ) -> None:
        """BA-5749: offset pagination total_count must equal distinct role count, not JOIN-inflated count."""
        querier = BatchQuerier(
            conditions=[],
            orders=[RoleOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        assert len(result.items) == 2
        assert result.total_count == 2

    async def test_total_count_not_inflated_with_cursor_pagination(
        self,
        repository: PermissionControllerRepository,
        roles_with_object_permissions: list[CreatedRole],
    ) -> None:
        """BA-5749: cursor pagination total_count must equal distinct role count, not JOIN-inflated count."""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=CursorForwardPagination(
                first=10,
                cursor_order=RoleOrders.created_at(ascending=True),
            ),
        )

        result = await repository.search_roles(querier)

        assert len(result.items) == 2
        assert result.total_count == 2
