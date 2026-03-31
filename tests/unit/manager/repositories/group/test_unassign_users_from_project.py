"""Tests for GroupDBSource.unassign_users_from_project()"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.group.row import AssocGroupUserRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.group.db_source import GroupDBSource
from ai.backend.manager.repositories.group.scope_binders import UserProjectEntityUnbinder
from ai.backend.testutils.db import with_tables


class TestUnassignUsersFromProject:
    """Tests for GroupDBSource.unassign_users_from_project"""

    @pytest.fixture
    def test_password_info(self) -> PasswordInfo:
        return PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AssocGroupUserRow,
                AssociationScopesEntitiesRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                    dotfiles=b"",
                    integration_id=None,
                )
            )
            await session.commit()
        return domain_name

    @pytest.fixture
    async def user_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            await session.commit()
        return policy_name

    @pytest.fixture
    async def test_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
    ) -> uuid.UUID:
        project_id = uuid.uuid4()
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            session.add(
                GroupRow(
                    id=project_id,
                    name=f"test-project-{project_id.hex[:8]}",
                    description="Test project",
                    is_active=True,
                    domain_name=test_domain,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=policy_name,
                    type=ProjectType.GENERAL,
                )
            )
            await session.commit()
        return project_id

    async def _create_user(
        self,
        db: ExtendedAsyncSAEngine,
        domain_name: str,
        policy_name: str,
        password_info: PasswordInfo,
    ) -> uuid.UUID:
        user_uuid = uuid.uuid4()
        async with db.begin_session() as session:
            session.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"user-{user_uuid.hex[:8]}",
                    email=f"user-{user_uuid.hex[:8]}@example.com",
                    password=password_info,
                    need_password_change=False,
                    full_name="Test User",
                    description="",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=policy_name,
                )
            )
            await session.commit()
        return user_uuid

    async def _assign_user(
        self,
        db: ExtendedAsyncSAEngine,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        async with db.begin_session() as session:
            session.add(
                AssocGroupUserRow(user_id=user_id, group_id=project_id),
            )
            await session.commit()

    @pytest.fixture
    async def assigned_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
        test_project: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create 3 users and assign them to test_project."""
        user_ids: list[uuid.UUID] = []
        for _ in range(3):
            uid = await self._create_user(
                db_with_cleanup, test_domain, user_resource_policy, test_password_info
            )
            await self._assign_user(db_with_cleanup, test_project, uid)
            user_ids.append(uid)
        return user_ids

    @pytest.fixture
    def group_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> GroupDBSource:
        return GroupDBSource(db=db_with_cleanup)

    # --- Test cases ---

    async def test_unassign_users_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        assigned_users: list[uuid.UUID],
    ) -> None:
        """Assigned users are unassigned and returned."""
        unbinder = UserProjectEntityUnbinder(
            user_uuids=assigned_users,
            project_id=test_project,
        )
        result = await group_db_source.unassign_users_from_project(unbinder)

        assert len(result.unassigned_users) == 3
        result_uuids = {u.uuid for u in result.unassigned_users}
        assert result_uuids == set(assigned_users)
        assert result.failures == []

        # Verify association rows removed
        async with db_with_cleanup.begin_readonly_session() as session:
            remaining = (
                await session.execute(
                    sa.select(AssocGroupUserRow).where(AssocGroupUserRow.group_id == test_project)
                )
            ).all()
            assert len(remaining) == 0

    async def test_unassign_nonexistent_users_reports_failures(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        assigned_users: list[uuid.UUID],
    ) -> None:
        """Non-existent user IDs are reported as failures."""
        fake_ids = [uuid.uuid4(), uuid.uuid4()]
        unbinder = UserProjectEntityUnbinder(
            user_uuids=fake_ids,
            project_id=test_project,
        )
        result = await group_db_source.unassign_users_from_project(unbinder)

        assert result.unassigned_users == []
        assert len(result.failures) == 2
        failure_ids = {f.user_id for f in result.failures}
        assert failure_ids == set(fake_ids)
        for f in result.failures:
            assert "does not exist" in f.reason

        # Verify original assignments are untouched
        async with db_with_cleanup.begin_readonly_session() as session:
            remaining = (
                await session.execute(
                    sa.select(AssocGroupUserRow).where(AssocGroupUserRow.group_id == test_project)
                )
            ).all()
            assert len(remaining) == 3

    async def test_unassign_existing_but_not_assigned_users_reports_failures(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
        test_project: uuid.UUID,
        assigned_users: list[uuid.UUID],
    ) -> None:
        """Users that exist but are not assigned to the project are reported as failures."""
        unassigned_user_id = await self._create_user(
            db_with_cleanup, test_domain, user_resource_policy, test_password_info
        )
        unbinder = UserProjectEntityUnbinder(
            user_uuids=[unassigned_user_id],
            project_id=test_project,
        )
        result = await group_db_source.unassign_users_from_project(unbinder)

        assert result.unassigned_users == []
        assert len(result.failures) == 1
        assert result.failures[0].user_id == unassigned_user_id
        assert "not assigned" in result.failures[0].reason

    async def test_unassign_mixed_success_and_failures(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
        test_project: uuid.UUID,
        assigned_users: list[uuid.UUID],
    ) -> None:
        """Mixed request: assigned users are unassigned, others reported as failures."""
        fake_id = uuid.uuid4()
        unassigned_user_id = await self._create_user(
            db_with_cleanup, test_domain, user_resource_policy, test_password_info
        )
        mixed_ids = [assigned_users[0], fake_id, unassigned_user_id]

        unbinder = UserProjectEntityUnbinder(
            user_uuids=mixed_ids,
            project_id=test_project,
        )
        result = await group_db_source.unassign_users_from_project(unbinder)

        assert len(result.unassigned_users) == 1
        assert result.unassigned_users[0].uuid == assigned_users[0]
        assert len(result.failures) == 2
        failure_map = {f.user_id: f.reason for f in result.failures}
        assert "does not exist" in failure_map[fake_id]
        assert "not assigned" in failure_map[unassigned_user_id]
