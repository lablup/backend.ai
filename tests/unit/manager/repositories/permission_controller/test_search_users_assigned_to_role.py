"""
Tests for PermissionControllerRepository.search_users_assigned_to_role() functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import PasswordHashAlgorithm, PasswordInfo, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.permission_controller.options import (
    AssignedUserConditions,
    AssignedUserOrders,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.db import with_tables


def create_test_password_info(password: str = "test_password") -> PasswordInfo:
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=16,
    )


@dataclass
class CreatedUserAssignment:
    user_id: uuid.UUID
    username: str
    email: str
    role_id: uuid.UUID
    assignment_id: uuid.UUID
    granted_at: datetime


class TestSearchUsersAssignedToRole:
    """Tests for searching users assigned to a role."""

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                PermissionRow,
                ObjectPermissionRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        return PermissionControllerRepository(db_with_tables)

    @pytest.fixture
    async def created_users_and_assignments(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> list[CreatedUserAssignment]:
        """Create domain, policy, role, users, and role assignments."""
        created: list[CreatedUserAssignment] = []
        base_time = datetime(2026, 1, 1, tzinfo=UTC)

        async with db_with_tables.begin_session() as db_sess:
            domain = DomainRow(
                name="test-domain",
                description="Test domain",
                is_active=True,
            )
            db_sess.add(domain)

            policy = UserResourcePolicyRow(
                name="test-policy",
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            db_sess.add(policy)
            await db_sess.flush()

            role = RoleRow(name="test-role", description="Test role")
            db_sess.add(role)
            await db_sess.flush()

            users_data = [
                ("alice", "alice@example.com"),
                ("bob", "bob@test.org"),
                ("charlie", "charlie@example.com"),
            ]

            for i, (username, email) in enumerate(users_data):
                user_id = uuid.uuid4()
                user = UserRow(
                    uuid=user_id,
                    username=username,
                    email=email,
                    password=create_test_password_info(),
                    domain_name="test-domain",
                    resource_policy="test-policy",
                    status=UserStatus.ACTIVE,
                    need_password_change=False,
                )
                db_sess.add(user)
                await db_sess.flush()

                granted_at = base_time + timedelta(minutes=i)
                assignment = UserRoleRow(
                    user_id=user_id,
                    role_id=role.id,
                    granted_at=granted_at,
                )
                db_sess.add(assignment)
                await db_sess.flush()

                created.append(
                    CreatedUserAssignment(
                        user_id=user_id,
                        username=username,
                        email=email,
                        role_id=role.id,
                        assignment_id=assignment.id,
                        granted_at=assignment.granted_at,
                    )
                )

        return created

    async def test_search_with_role_id_filter(
        self,
        repository: PermissionControllerRepository,
        created_users_and_assignments: list[CreatedUserAssignment],
    ) -> None:
        """Basic search filtering by role_id returns all assignments for the role."""
        role_id = created_users_and_assignments[0].role_id
        querier = BatchQuerier(
            conditions=[AssignedUserConditions.by_role_id(role_id)],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_users_assigned_to_role(querier)

        assert result.total_count == len(created_users_and_assignments)
        result_user_ids = {item.user_id for item in result.items}
        expected_user_ids = {a.user_id for a in created_users_and_assignments}
        assert result_user_ids == expected_user_ids

    async def test_role_id_isolation(
        self,
        repository: PermissionControllerRepository,
        created_users_and_assignments: list[CreatedUserAssignment],
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """Searching with a different role_id should not return assignments from the test role."""
        async with db_with_tables.begin_session() as db_sess:
            other_role = RoleRow(name="other-role", description="Other role")
            db_sess.add(other_role)
            await db_sess.flush()
            other_role_id = other_role.id

        querier = BatchQuerier(
            conditions=[AssignedUserConditions.by_role_id(other_role_id)],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_users_assigned_to_role(querier)

        assert result.total_count == 0
        assert len(result.items) == 0

    async def test_username_filter_exact_match(
        self,
        repository: PermissionControllerRepository,
        created_users_and_assignments: list[CreatedUserAssignment],
    ) -> None:
        """EXISTS subquery filtering by exact username match."""
        role_id = created_users_and_assignments[0].role_id
        querier = BatchQuerier(
            conditions=[
                AssignedUserConditions.by_role_id(role_id),
                AssignedUserConditions.exists_user_combined([
                    AssignedUserConditions.by_username_equals(
                        StringMatchSpec(value="alice", case_insensitive=False, negated=False)
                    ),
                ]),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_users_assigned_to_role(querier)

        assert result.total_count == 1
        assert result.items[0].user_id == created_users_and_assignments[0].user_id

    async def test_username_filter_contains(
        self,
        repository: PermissionControllerRepository,
        created_users_and_assignments: list[CreatedUserAssignment],
    ) -> None:
        """EXISTS subquery filtering by username contains."""
        role_id = created_users_and_assignments[0].role_id
        querier = BatchQuerier(
            conditions=[
                AssignedUserConditions.by_role_id(role_id),
                AssignedUserConditions.exists_user_combined([
                    AssignedUserConditions.by_username_contains(
                        StringMatchSpec(value="li", case_insensitive=False, negated=False)
                    ),
                ]),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_users_assigned_to_role(querier)

        # "alice" and "charlie" contain "li"
        assert result.total_count == 2
        result_user_ids = {item.user_id for item in result.items}
        expected = {a.user_id for a in created_users_and_assignments if "li" in a.username}
        assert result_user_ids == expected

    async def test_email_filter_ends_with(
        self,
        repository: PermissionControllerRepository,
        created_users_and_assignments: list[CreatedUserAssignment],
    ) -> None:
        """EXISTS subquery filtering by email ends_with."""
        role_id = created_users_and_assignments[0].role_id
        querier = BatchQuerier(
            conditions=[
                AssignedUserConditions.by_role_id(role_id),
                AssignedUserConditions.exists_user_combined([
                    AssignedUserConditions.by_email_ends_with(
                        StringMatchSpec(value="@test.org", case_insensitive=False, negated=False)
                    ),
                ]),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_users_assigned_to_role(querier)

        # Only bob@test.org
        assert result.total_count == 1
        assert result.items[0].user_id == created_users_and_assignments[1].user_id

    async def test_combined_username_and_email_filter(
        self,
        repository: PermissionControllerRepository,
        created_users_and_assignments: list[CreatedUserAssignment],
    ) -> None:
        """Combined username + email conditions in single EXISTS subquery."""
        role_id = created_users_and_assignments[0].role_id
        querier = BatchQuerier(
            conditions=[
                AssignedUserConditions.by_role_id(role_id),
                AssignedUserConditions.exists_user_combined([
                    AssignedUserConditions.by_username_contains(
                        StringMatchSpec(value="alice", case_insensitive=False, negated=False)
                    ),
                    AssignedUserConditions.by_email_ends_with(
                        StringMatchSpec(value="@example.com", case_insensitive=False, negated=False)
                    ),
                ]),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_users_assigned_to_role(querier)

        # Only alice matches both username contains "alice" AND email ends with "@example.com"
        assert result.total_count == 1
        assert result.items[0].user_id == created_users_and_assignments[0].user_id

    async def test_order_by_granted_at(
        self,
        repository: PermissionControllerRepository,
        created_users_and_assignments: list[CreatedUserAssignment],
    ) -> None:
        """Results ordered by granted_at ascending."""
        role_id = created_users_and_assignments[0].role_id
        querier = BatchQuerier(
            conditions=[AssignedUserConditions.by_role_id(role_id)],
            orders=[AssignedUserOrders.granted_at(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_users_assigned_to_role(querier)

        result_user_ids = [item.user_id for item in result.items]
        expected_user_ids = [
            a.user_id for a in sorted(created_users_and_assignments, key=lambda a: a.granted_at)
        ]
        assert result_user_ids == expected_user_ids

    async def test_offset_pagination(
        self,
        repository: PermissionControllerRepository,
        created_users_and_assignments: list[CreatedUserAssignment],
    ) -> None:
        """Offset pagination returns correct subset."""
        role_id = created_users_and_assignments[0].role_id
        querier = BatchQuerier(
            conditions=[AssignedUserConditions.by_role_id(role_id)],
            orders=[AssignedUserOrders.granted_at(ascending=True)],
            pagination=OffsetPagination(limit=2, offset=0),
        )

        result = await repository.search_users_assigned_to_role(querier)

        assert len(result.items) == 2
        assert result.total_count == 3
        assert result.has_next_page is True

        # Second page
        querier_page2 = BatchQuerier(
            conditions=[AssignedUserConditions.by_role_id(role_id)],
            orders=[AssignedUserOrders.granted_at(ascending=True)],
            pagination=OffsetPagination(limit=2, offset=2),
        )

        result_page2 = await repository.search_users_assigned_to_role(querier_page2)

        assert len(result_page2.items) == 1
        assert result_page2.total_count == 3
        assert result_page2.has_next_page is False

    async def test_empty_result(
        self,
        repository: PermissionControllerRepository,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """Search with no matching assignments returns empty result."""
        nonexistent_role_id = uuid.uuid4()
        querier = BatchQuerier(
            conditions=[AssignedUserConditions.by_role_id(nonexistent_role_id)],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_users_assigned_to_role(querier)

        assert result.total_count == 0
        assert len(result.items) == 0
        assert result.has_next_page is False
        assert result.has_previous_page is False
