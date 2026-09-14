"""Tests for PermissionControllerRepository.search_role_assignments_in_scope() against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.permission import RoleNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role.scopes import (
    RoleRoleAssignmentOperationScope,
    UserRoleAssignmentOperationScope,
)
from ai.backend.manager.models.rbac_models.user_role.searchers import RoleAssignmentSearcher
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user import PasswordHashAlgorithm, PasswordInfo, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.db import with_tables

# Rows reachable through string relationships; kept registered for configure_mappers().
_ORM_CLUSTER = (
    AgentRow,
    ResourceGroupForDomainRow,
    ImageRow,
)


@dataclass
class SeededAssignments:
    alice: UserID
    bob: UserID
    charlie: UserID
    role_a: RoleID
    role_b: RoleID


class TestSearchRoleAssignmentsInScope:
    """Assignment rows read through user and role operation scopes."""

    @pytest.fixture
    async def db_with_tables(
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
                UserRow,
                KeyPairRow,
                UserRoleRow,
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
    def searcher(self) -> RoleAssignmentSearcher:
        return RoleAssignmentSearcher(pagination=OffsetPagination(limit=10, offset=0))

    @pytest.fixture
    async def seeded(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> SeededAssignments:
        """alice holds role_a and role_b, bob holds role_a, charlie holds none."""
        domain_id = DomainID(uuid.uuid4())
        async with db_with_tables.begin_session() as db_sess:
            db_sess.add(DomainRow(id=domain_id, name="test-domain", description="", is_active=True))
            db_sess.add(
                UserResourcePolicyRow(
                    name="test-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            await db_sess.flush()

            role_a = RoleRow(scope_type=ProjectEntityType(), scope_id=uuid.uuid4(), name="role-a")
            role_b = RoleRow(scope_type=ProjectEntityType(), scope_id=uuid.uuid4(), name="role-b")
            db_sess.add_all([role_a, role_b])
            await db_sess.flush()

            user_ids: dict[str, UserID] = {}
            for username in ("alice", "bob", "charlie"):
                user_id = UserID(uuid.uuid4())
                db_sess.add(
                    UserRow(
                        uuid=user_id,
                        username=username,
                        email=f"{username}@example.com",
                        password=PasswordInfo(
                            password="test_password",
                            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                            rounds=100_000,
                            salt_size=16,
                        ),
                        domain_name="test-domain",
                        resource_policy="test-policy",
                        status=UserStatus.ACTIVE,
                        need_password_change=False,
                        domain_id=domain_id,
                    )
                )
                user_ids[username] = user_id
            await db_sess.flush()

            db_sess.add_all([
                UserRoleRow(user_id=user_ids["alice"], role_id=role_a.id),
                UserRoleRow(user_id=user_ids["alice"], role_id=role_b.id),
                UserRoleRow(user_id=user_ids["bob"], role_id=role_a.id),
            ])

        return SeededAssignments(
            alice=user_ids["alice"],
            bob=user_ids["bob"],
            charlie=user_ids["charlie"],
            role_a=RoleID(role_a.id),
            role_b=RoleID(role_b.id),
        )

    async def test_user_scope_reads_the_roles_one_user_holds(
        self,
        repository: PermissionControllerRepository,
        searcher: RoleAssignmentSearcher,
        seeded: SeededAssignments,
    ) -> None:
        result = await repository.search_role_assignments_in_scope(
            [UserRoleAssignmentOperationScope(user_id=seeded.alice)], searcher
        )

        assert result.total_count == 2
        assert {(item.user_id, item.role_id) for item in result.items} == {
            (seeded.alice, seeded.role_a),
            (seeded.alice, seeded.role_b),
        }

    async def test_role_scope_reads_the_users_holding_one_role(
        self,
        repository: PermissionControllerRepository,
        searcher: RoleAssignmentSearcher,
        seeded: SeededAssignments,
    ) -> None:
        result = await repository.search_role_assignments_in_scope(
            [RoleRoleAssignmentOperationScope(role_id=seeded.role_a)], searcher
        )

        assert result.total_count == 2
        assert {(item.user_id, item.role_id) for item in result.items} == {
            (seeded.alice, seeded.role_a),
            (seeded.bob, seeded.role_a),
        }

    async def test_scopes_are_combined_with_or(
        self,
        repository: PermissionControllerRepository,
        searcher: RoleAssignmentSearcher,
        seeded: SeededAssignments,
    ) -> None:
        result = await repository.search_role_assignments_in_scope(
            [
                UserRoleAssignmentOperationScope(user_id=seeded.bob),
                RoleRoleAssignmentOperationScope(role_id=seeded.role_b),
            ],
            searcher,
        )

        assert result.total_count == 2
        assert [(item.user_id, item.role_id) for item in result.items].count((
            seeded.bob,
            seeded.role_a,
        )) == 1
        assert {(item.user_id, item.role_id) for item in result.items} == {
            (seeded.bob, seeded.role_a),
            (seeded.alice, seeded.role_b),
        }

    async def test_role_scope_naming_a_missing_role_raises(
        self,
        repository: PermissionControllerRepository,
        searcher: RoleAssignmentSearcher,
        seeded: SeededAssignments,
    ) -> None:
        with pytest.raises(RoleNotFound):
            await repository.search_role_assignments_in_scope(
                [RoleRoleAssignmentOperationScope(role_id=RoleID(uuid.uuid4()))], searcher
            )

    async def test_user_scope_without_assignments_is_empty(
        self,
        repository: PermissionControllerRepository,
        searcher: RoleAssignmentSearcher,
        seeded: SeededAssignments,
    ) -> None:
        result = await repository.search_role_assignments_in_scope(
            [UserRoleAssignmentOperationScope(user_id=seeded.charlie)], searcher
        )

        assert result.total_count == 0
        assert result.items == []
